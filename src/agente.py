import logging
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import monotonic

import httpx
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from pydantic import BaseModel

from .config import DATA, custom_resume, live_model
from .executor import make_executor, scripted_model
from .memoria import Session
from .models import ChatOut, Pedido, Recomendacao, ToolCall
from .prompts import avaliar_fit, perfil_chain
from .rag import default_index, index_for_resume, read_pdf, retrieve
from .repository import Repository, fixtures
from .rules import geo, interpretar, plain, restrictions, salario
from .tools import Providers
from .verificador import verify

logger = logging.getLogger(__name__)


def output_text(output):
    """AgentExecutor returns content blocks for reasoning models; keep only the text blocks."""
    if isinstance(output, list):
        return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in output)
    return str(output)


class Claim(BaseModel):
    job_id: str
    claim: str


class Draft(BaseModel):
    claims: list[Claim]


class Radar:
    def __init__(self, *, dummy=True, db_path=DATA / "runtime" / "vagas.db", use_nli=True, index_path=None, llm=None):
        self.dummy, self.use_nli = dummy, use_nli
        resume = custom_resume() if not dummy else None
        self.index_path = index_path or (index_for_resume(resume, not dummy) if resume else default_index(not dummy))
        self.llm = llm if llm is not None else (None if dummy else live_model())
        self.repo = Repository(db_path.resolve())
        self.providers = Providers(dummy, fixtures(DATA) if dummy else [])
        if dummy:
            self.repo.save(self.providers.fixtures)
        self.sessions = {}
        self.lock = Lock()
        text = read_pdf(resume) if resume else (DATA / "curriculo.txt").read_text()
        self.profile = perfil_chain(self.llm).invoke({"curriculo": text})
        self.chain = RunnableWithMessageHistory(
            RunnableLambda(self._turn), self._history, input_messages_key="message",
            history_messages_key="chat_history", output_messages_key="history_answer",
        )

    def session(self, session_id):
        with self.lock:
            return self.sessions.setdefault(session_id, Session(real=not self.dummy))

    def record_application(self, session_id, job_id, status):
        session = self.session(session_id)
        with session.lock:
            if job_id not in session.jobs:
                raise KeyError(job_id)
            self.repo.candidatura(session_id, job_id, status)

    def _history(self, session_id):
        return self.session(session_id).history

    def chat(self, session_id, message):
        session = self.session(session_id)
        with session.lock:
            session.trim(self.llm)
            return self.chain.invoke({"session_id": session_id, "message": message},
                                     config={"configurable": {"session_id": session_id}})["response"]

    def _intent(self, message, session):
        if not self.llm:
            return interpretar(message)
        local = interpretar(message)
        try:
            parsed = self.llm.with_structured_output(Pedido).invoke(
                "Classifique a intenção e extraia apenas restrições explícitas do pedido em português. "
                "Use null para omissões. Se houver salário sem período, use mês. "
                "Converta ordinais em posição. Comparação com currículo é curriculo. "
                f"Resumo da sessão: {session.summary}\nPedido: {message}")
            if local.entidades.posicao:
                parsed.entidades.posicao = local.entidades.posicao
            return parsed
        except Exception:
            logger.warning("Interpretação estruturada indisponível; usando regras locais.")
            return local

    def _sql(self, message, session_id):
        if self.llm:
            from langchain_classic.chains import create_sql_query_chain
            from langchain_community.utilities import SQLDatabase
            from sqlalchemy import create_engine

            db = SQLDatabase(create_engine("sqlite:///" + self.repo.path.as_posix()),
                             include_tables=["vagas", "candidaturas"], sample_rows_in_table_info=0)
            question = message + ("\nInclua title e company no SELECT. "
                                  "Tabela candidaturas: use somente vaga_id e status, pois o executor "
                                  "já filtra a sessão. 'Já apliquei' corresponde a status 'enviada'. "
                                  "Sem período explícito, interprete salário como mensal.")
            query = create_sql_query_chain(self.llm, db, k=10).invoke({"question": question})
            # Reasoning models reject `stop`, so the reply may echo Question/SQLResult/Answer; keep only the SQL.
            fenced = re.search(r"```(?:sql)?\s*(.*?)```", query, flags=re.S | re.I)
            query = fenced.group(1) if fenced else re.split(r"\n\s*SQLResult:", query.split("SQLQuery:")[-1])[0]
            query = query.strip()
            return query, self.repo.query(query, session_id)
        entities = interpretar(message).entidades
        clauses, params = [], []
        if entities.salario_min is not None:
            clauses.append("v.salary_min > ? AND v.currency = ? AND v.period = ?")
            params.extend([entities.salario_min, entities.moeda, entities.periodo])
        if "apliquei" in plain(message):
            clauses.append("NOT EXISTS (SELECT 1 FROM candidaturas c WHERE c.vaga_id=v.id AND c.status='enviada')")
        else:
            clauses.append("EXISTS (SELECT 1 FROM candidaturas c WHERE c.vaga_id=v.id)")
        query = ("SELECT v.id,v.title,v.company,v.salary_min,v.currency,v.period FROM vagas v WHERE "
                 + " AND ".join(clauses) + " ORDER BY v.salary_min DESC")
        return query, self.repo.query(query, session_id, params)

    def _turn(self, inputs):
        session_id, message = inputs["session_id"], inputs["message"]
        session = self.session(session_id)
        pedido = self._intent(message, session)
        intent = pedido.intencao
        query_text = plain(message)
        compare_search = (interpretar(message).intencao == "busca"
                          and bool(re.search(r"curriculo|compare|aderencia", query_text)))
        if compare_search:
            intent = "busca"
        if intent == "busca":
            updates = pedido.entidades.model_dump(exclude_none=True, exclude={"posicao"})
            session.entities = session.entities.model_copy(update=updates)
        target_pos = pedido.entidades.posicao or 1
        target = session.jobs.get(session.visible[target_pos - 1]) if target_pos <= len(session.visible) else None
        traces, checks, cards, results = [], [], [], {}
        memories = session.retrieve(message)

        def log(name, start, status, detail, source=""):
            traces.append(ToolCall(name=name, status=status, detail=detail, source=source,
                                   duration_ms=round((monotonic() - start) * 1000)))
            logger.info("tool=%s source=%s status=%s", name, source, status)

        @tool
        def buscar_vagas() -> list:
            """Busca vagas reais ou simuladas segundo os filtros desta sessão."""
            if "jobs" not in results:
                jobs, calls = self.providers.buscar(session.entities.stack or session.entities.cargo or "")
                self.repo.save(jobs)
                traces.extend(calls)
                for call in calls:
                    logger.info("tool=%s source=%s status=%s", call.name, call.source, call.status)
                results["jobs"] = jobs
            return [j.model_dump(include={"id", "title", "location", "description"}) |
                    {"description": j.description[:600]} for j in results["jobs"][:12]]

        @tool
        def converter_moeda() -> str:
            """Converte para BRL o salário da vaga identificada no histórico."""
            if "conversion" in results:
                return results["conversion"]
            start = monotonic()
            pay = salario(target) if target else None
            if not target:
                answer = (f"A última lista desta sessão tem {len(session.visible)} vaga(s) numerada(s); "
                          "escolha uma delas." if session.visible else
                          "Não encontrei essa posição na última lista desta sessão. Busque vagas primeiro.")
            elif not pay:
                answer = f"O anúncio de {target.title} não informa salário com moeda e período verificáveis."
            else:
                try:
                    rate, date, source = self.providers.cotacao(pay.currency)
                    original = f"{pay.currency} {pay.low:,.2f}"
                    brl = f"R$ {pay.low * rate:,.2f}"
                    if pay.high is not None:
                        original += f" a {pay.high:,.2f}"
                        brl += f" a R$ {pay.high * rate:,.2f}"
                    period = "mês" if pay.period == "month" else "ano"
                    answer = f"{target.title}: {original} por {period} ≈ {brl} por {period}. {source}"
                    answer += f" de {date} (1 {pay.currency} = R$ {rate})." if date else "."
                    log("converter_moeda", start, "dummy" if self.dummy else "ok", answer, source)
                    results["conversion"] = answer
                    return answer
                except (httpx.HTTPError, KeyError, ArithmeticError, ValueError):
                    answer = "O câmbio está indisponível. O salário original não foi convertido."
            log("converter_moeda", start, "incerto", answer)
            results["conversion"] = answer
            return answer

        @tool
        def recuperar_contexto() -> list:
            """Recupera do índice documental os trechos do currículo que ajudam neste pedido."""
            if "context" in results:
                return results["context"]
            start = monotonic()
            try:
                matches = retrieve(message, kind="curriculo", index_path=self.index_path, real=not self.dummy)
            except Exception:
                matches = None
            log("recuperar_contexto", start, "ok" if matches else "indisponível",
                matches[0]["trecho"][:700] if matches else "Índice documental indisponível. Execute o notebook 01.",
                "FAISS documental")
            results["context"] = matches or []
            return results["context"]

        @tool
        def consultar_candidaturas() -> list:
            """Consulta as vagas e as candidaturas desta sessão em modo somente leitura."""
            if "rows" in results:
                return results["rows"]
            start = monotonic()
            try:
                query, rows = self._sql(message, session_id)
                log("consultar_candidaturas", start, "ok", f"{query} | {len(rows)} linha(s).", "SQLite")
            except Exception as exc:
                logger.warning("Consulta indisponível: %s", type(exc).__name__)
                rows = []
                log("consultar_candidaturas", start, "erro", "Não foi possível executar a consulta.", "SQLite")
            results["rows"] = rows
            return rows

        routes = {"busca": buscar_vagas, "cambio": converter_moeda, "curriculo": recuperar_contexto,
                  "carta": recuperar_contexto, "candidaturas": consultar_candidaturas}
        preliminary = {}
        if intent in routes:
            selected = routes[intent]
            extra = (recuperar_contexto.name,) if compare_search else ()
            executor = make_executor(self.llm or scripted_model(selected.name, also=extra),
                                     list({route.name: route for route in routes.values()}.values()))
            try:
                actions = ", ".join((selected.name, *extra))
                proposal = executor.invoke({"input": f"Intenção: {intent}. Use estas ferramentas: {actions}. "
                                            f"Pedido: {message}\nResumo: {session.summary}\nMemória: {memories}",
                                            "chat_history": inputs["chat_history"]})
                if intent == "busca":
                    preliminary = {c.job_id: c.claim[:280] for c in Draft.model_validate(
                        JsonOutputParser().parse(output_text(proposal["output"]))).claims[:12]}
            except Exception:
                logger.warning("Proposta do agente indisponível; usando percurso determinístico.")
            # Tool calls are idempotent within a turn. Fill the required result if the model skipped it.
            selected.invoke({})
            if compare_search:
                recuperar_contexto.invoke({})

        if intent == "busca":
            jobs = results["jobs"]
            ranked = []
            discarded, pending = 0, 0
            for job in jobs:
                verdict, evidence, reason = restrictions(job, session.entities, self.profile)
                fit = avaliar_fit.invoke((self.profile, f"{job.title} {job.description}"))
                ranked.append((job, verdict, evidence, reason, fit))
            order = {"recomendado": 0, "pendente": 1, "descartado": 2}
            ranked.sort(key=lambda x: (order[x[1]], -len(x[4]["skills"]), -int(x[4]["senioridade"]), x[0].id))
            facts = [f"Perfil: {self.profile.model_dump_json()[:700]}"]
            if session.entities.aceita_brasil:
                facts.append("Regra procedural: mostrar na lista numerada apenas vagas confirmadas para Brasil.")
            def claim_for(job):
                return preliminary.get(job.id) or ("Applicants based in Brazil are eligible." if
                    geo(job)[0] != "descartado" or (self.dummy and job.id == "demo-atlas") else
                    "Applicants based in Brazil are not eligible.")
            shown = [item[0] for item in ranked[:10]]
            # In real mode each verification makes LLM calls; run them concurrently, keep the order.
            with ThreadPoolExecutor(max_workers=5) as pool:
                verified = dict(zip([j.id for j in shown], pool.map(
                    lambda job: verify(job, claim_for(job), self.llm, use_nli=self.use_nli), shown)))
            for job, verdict, evidence, reason, fit in ranked[:10]:
                status = geo(job)[0]
                checked = verified[job.id]
                if checked.status == "contradita" and verdict == "recomendado":
                    verdict, reason = "pendente", "A afirmação preliminar não passou na verificação."
                if checked.status == "contradita" and status == "descartado":
                    checked.reason += " Correção aplicada: vaga excluída da lista."
                checks.append(checked)
                if verdict == "recomendado" and fit["skills"]:
                    reason += " Aderência ao currículo: " + ", ".join(fit["skills"]) + "."
                pay = salario(job)
                salary = (f"{pay.currency} {pay.low:,.2f}" + (f" a {pay.high:,.2f}" if pay.high is not None else "")
                          + (" / mês" if pay.period == "month" else " / ano")) if pay else None
                cards.append(Recomendacao(id=job.id, title=job.title, company=job.company, source=job.source,
                                          url=job.url, status=verdict, reason=reason, evidence=evidence,
                                          skills=fit["skills"], salary=salary))
                if verdict == "descartado":
                    discarded += 1
                    facts.append(f"Vaga descartada: {job.title}. {reason} Trecho: {evidence[:120]}")
                pending += verdict == "pendente"
            visible = [c for c in cards if c.status == "recomendado"]
            session.visible = [c.id for c in visible]
            session.jobs = {j.id: j for j in jobs}
            session.remember(facts)
            lines = [f"{len(visible)} vaga(s) recomendada(s); {pending} pendente(s); {discarded} descartada(s) na amostra exibida."]
            lines.extend(f"{i}. {c.title} · {c.company}." for i, c in enumerate(visible, 1))
            if session.entities.aceita_brasil:
                lines.append("A lista numerada inclui apenas vagas com elegibilidade confirmada para o Brasil. Os demais casos aparecem como evidência.")
            searches = [t for t in traces if t.name == "buscar_vagas"]
            failed = sorted({t.source for t in searches if t.status == "erro"})
            stale = sorted({t.source for t in searches if t.status == "cache desatualizado"})
            used = sorted({t.source for t in searches if t.status != "erro"})
            if failed:
                lines.append(f"Fonte indisponível: {', '.join(failed)}. "
                             + (f"Continuei com {', '.join(used)}; confira a trilha." if used else "Nenhuma fonte respondeu."))
            if stale:
                lines.append(f"{', '.join(stale)} respondeu com cache desatualizado; confira a trilha.")
            if compare_search:
                context = results["context"]
                if visible and context:
                    best = visible[0]
                    overlap = ", ".join(best.skills) or "sem correspondência explícita"
                    lines.append(f"Melhor aderência ao currículo: {best.title}. Habilidades em comum: {overlap}.")
                    checks.append({"job_id": best.id, "claim": "Habilidades cruzadas entre anúncio e currículo",
                                   "status": "confirmada" if best.skills else "incerta",
                                   "evidence": f"Currículo: {context[0]['trecho'][:400]}\nAnúncio: {session.jobs[best.id].description[:450]}",
                                   "reason": f"Interseção explícita: {overlap}."})
                elif not context:
                    lines.append("O índice documental está indisponível para comparação.")
            answer = "\n".join(lines)
        elif intent == "cambio":
            answer = results["conversion"]
            if target and (pay := salario(target)):
                checks.append({"job_id": target.id, "claim": f"Salário em {pay.currency} por {pay.period}",
                               "status": "confirmada", "evidence": pay.evidence,
                               "reason": "Moeda e período extraídos do anúncio; a conversão usa a cotação exibida quando disponível."})
        elif intent in {"curriculo", "carta"}:
            context = results["context"]
            if not target:
                answer = "Busque vagas primeiro para comparar com o currículo ou pedir uma carta."
            elif not context:
                answer = "O índice documental está indisponível. Execute o notebook 01 para comparar com evidência."
            else:
                fits = [(session.jobs[id], avaliar_fit.invoke((self.profile, session.jobs[id].description)))
                        for id in session.visible]
                chosen, fit = (target, avaliar_fit.invoke((self.profile, target.description))) if (
                    pedido.entidades.posicao or intent == "carta") else max(
                    fits, key=lambda item: (len(item[1]["skills"]), item[1]["senioridade"]))
                overlap = ", ".join(fit["skills"]) or "nenhuma habilidade explícita em comum"
                answer = (f"{chosen.title} é a melhor correspondência da lista atual. Habilidades em comum: {overlap}."
                          if not pedido.entidades.posicao else f"{chosen.title}. Habilidades em comum: {overlap}.")
                if intent == "carta":
                    answer = (f"Rascunho para {chosen.company}: Olá! Tenho interesse na vaga {chosen.title}. "
                              f"Gostaria de conversar sobre como minha experiência pode contribuir para a equipe. "
                              + (f"Habilidades em comum com a descrição: {overlap}." if fit["skills"] else ""))
                checks.append({"job_id": chosen.id, "claim": "Habilidades cruzadas entre anúncio e currículo",
                               "status": "confirmada", "evidence": f"Currículo: {context[0]['trecho'][:400]}\nAnúncio: {chosen.description[:450]}",
                               "reason": f"Interseção explícita: {overlap}."})
        elif intent == "candidaturas":
            rows = results["rows"]
            def describe(row):
                company = row.get("company") or getattr(session.jobs.get(row.get("id")), "company", None)
                return " · ".join(filter(None, [row.get("title", str(row)), company]))
            answer = (f"{len(rows)} vaga(s) encontrada(s):\n" + "\n".join(describe(row) for row in rows) if rows else
                      "Nenhuma vaga atende à consulta ou a consulta está indisponível. Confira a trilha.")
        else:
            answer = "Posso buscar vagas, filtrar por Brasil, converter o salário, comparar com o currículo ou consultar candidaturas."

        response = ChatOut(answer=answer, recommendations=cards, tool_calls=traces, verification=checks,
                           mode="dummy" if self.dummy else "real")
        return {"response": response, "history_answer": answer}
