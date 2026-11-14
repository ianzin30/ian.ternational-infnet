import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from threading import Lock
from time import monotonic
from typing import Literal

import httpx
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from pydantic import BaseModel

from .config import DATA, custom_resume, live_model
from .eventos import Emissor, ToolLog, contar_tokens, em_fila
from .executor import make_executor, scripted_model
from .memoria import Session
from .memoria_longa import MemoriaLonga, extrair_por_regras, skills_evitadas
from .models import ChatOut, Pedido, Recomendacao, ToolCall
from .prompts import AGENT_SYSTEM, avaliar_fit, perfil_chain, resposta_chain, skills_in
from .rag import build_index, default_index, index_for_resume, read_pdf, retrieve, termos_em_ingles
from .repository import Repository, fixtures
from .roteador import ROTAS, RoteadorVagas
from .rules import geo, interpretar, plain, restrictions, salario
from .tools import Providers
from .verificador import MODEL as NLI_MODEL, verify

logger = logging.getLogger(__name__)
LIMIAR_RECUPERACAO = 0.45  # below this similarity the first retrieval is treated as off-topic
COMPOSICAO = {
    "busca": "RunnableParallel(Remotive ∥ Arbeitnow) → restrictions → avaliar_fit.batch (@chain) → verify (NLI) → resposta_chain.stream",
    "cambio": "resolver referência no histórico → converter_moeda (AwesomeAPI) → resposta_chain.stream",
    "curriculo": "recuperar_contexto (FAISS) → avaliar_fit (@chain) → resposta_chain.stream",
    "carta": "recuperar_contexto (FAISS) → avaliar_fit (@chain) → resposta_chain.stream",
    "candidaturas": "create_sql_query_chain → SQLite somente leitura → resposta_chain.stream",
    "ajuda": "resposta_chain.stream",
}


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


class CurriculoInvalido(ValueError):
    pass


class Radar:
    def __init__(self, *, dummy=True, db_path=DATA / "runtime" / "vagas.db", use_nli=True, index_path=None, llm=None,
                 use_personal_resume=True):
        self.dummy, self.use_nli = dummy, use_nli
        self.llm = llm if llm is not None else (None if dummy else live_model())
        self.repo = Repository(db_path.resolve())
        self.memoria = MemoriaLonga(db_path.resolve().parent / "memoria.db", real=not dummy)
        self.uploads = db_path.resolve().parent / "uploads"
        self.providers = Providers(dummy, fixtures(DATA) if dummy else [])
        if dummy:
            self.repo.save(self.providers.fixtures)
        self.sessions = {}
        self.lock = Lock()
        self._fixed_index = index_path
        self.pessoal = custom_resume() if not dummy and use_personal_resume else None
        self.carregar_curriculo(self.pessoal, "pessoal" if self.pessoal else "ficticio", build=False)
        self.chain = RunnableWithMessageHistory(
            RunnableLambda(self._turn), self._history, input_messages_key="message",
            history_messages_key="chat_history", output_messages_key="history_answer",
        )

    # ---- currículo -------------------------------------------------------------------------
    def carregar_curriculo(self, path, origem, *, emit=None, build=True):
        """Lê o PDF, garante o índice FAISS e extrai o perfil. Só troca o estado se tudo der certo."""
        emit = emit or Emissor()
        real = not self.dummy
        emit.inicio("lendo", "Docling")
        if path:
            try:
                text = read_pdf(path)
            except Exception as exc:
                emit.fim("lendo", "erro", source="Docling")
                raise CurriculoInvalido("sem-texto") from exc
            if len(re.sub(r"\s+", "", text)) < 40:
                emit.fim("lendo", "erro", source="Docling")
                raise CurriculoInvalido("sem-texto")
        else:
            text = (DATA / "curriculo.txt").read_text()
        emit.fim("lendo", source="Docling", data={"caracteres": len(text)})
        emit.inicio("indexando", "FAISS")
        index = self._fixed_index or (index_for_resume(path, real) if path else default_index(real))
        chunks = None
        if build and path and not (index / "index.faiss").is_file():
            chunks = build_index(fixtures(DATA), path, index, real=real)
        emit.fim("indexando", source="FAISS", data={"trechos": chunks, "indice": index.name,
                                                    "reaproveitado": chunks is None})
        emit.inicio("extraindo", "OpenAI" if self.llm else "regras locais")
        profile = perfil_chain(self.llm).invoke({"curriculo": text})
        emit.fim("extraindo", source="OpenAI" if self.llm else "regras locais",
                 data={"perfil": profile.model_dump(), "parser": "JsonOutputParser → PerfilCandidato"})
        self.curriculo, self.origem, self.index_path, self.profile = path, origem, index, profile

    def arquivo_curriculo(self):
        return self.curriculo or DATA / "curriculo.pdf"

    def info_curriculo(self):
        path = self.arquivo_curriculo()
        pages = None
        try:
            import pypdfium2
            pdf = pypdfium2.PdfDocument(str(path))
            pages = len(pdf)
            pdf.close()
        except Exception:
            pass
        name = {"pessoal": "curriculo-pessoal.pdf", "ficticio": "curriculo-ficticio.pdf"}.get(self.origem) or getattr(
            self, "nome_enviado", path.name)
        return {"nome": name, "origem": self.origem, "paginas": pages, "skills": self.profile.skills,
                "senioridade": self.profile.senioridade, "tamanho": path.stat().st_size if path.exists() else None,
                "pode_restaurar": self.origem == "enviado"}

    def enviar_curriculo(self, content, nome, emit=None):
        self.uploads.mkdir(parents=True, exist_ok=True)
        path = self.uploads / f"{sha256(content).hexdigest()[:24]}.pdf"
        path.write_bytes(content)
        with self.lock:
            sessions = list(self.sessions.values())
        self.carregar_curriculo(path, "enviado", emit=emit)
        self.nome_enviado = nome
        for session in sessions:  # shown positions and fit were computed with the previous profile
            session.visible = []
        return self.info_curriculo()

    def restaurar_curriculo(self):
        self.carregar_curriculo(self.pessoal, "pessoal" if self.pessoal else "ficticio")
        return self.info_curriculo()

    # ---- sessões e memória -----------------------------------------------------------------
    def session(self, session_id):
        with self.lock:
            return self.sessions.setdefault(session_id, Session(real=not self.dummy))

    def fechar_sessao(self, session_id):
        with self.lock:
            return self.sessions.pop(session_id, None) is not None

    def record_application(self, session_id, job_id, status, user_id="local"):
        session = self.session(session_id)
        with session.lock:
            if job_id not in session.jobs:
                raise KeyError(job_id)
            self.repo.candidatura(session_id, job_id, status)
            job = session.jobs[job_id]
        verb = {"salva": "Salvou a vaga", "enviada": "Aplicou para", "descartada": "Descartou a vaga"}[status]
        return self.memoria.guardar(user_id, "episódica", f"{verb} {job.title} · {job.company}",
                                    "ação na interface (POST /candidaturas)")

    def memoria_view(self, user_id, session_id=None):
        with self.lock:
            session = self.sessions.get(session_id) if session_id else None
        items = []
        if session:
            items += [{"tag": "preferência", "texto": p} for p in session.prefs]
            items += [{"tag": "filtro ativo", "texto": f"{k}: {v}"} for k, v in
                      session.entities.model_dump(exclude_none=True).items() if v not in ([], "")]
            if session.summary:
                items.append({"tag": "resumo", "texto": session.summary[-300:]})
            items += [{"tag": "fato da busca", "texto": fact[:200]} for fact in session.knowledge[-4:]]
        return {"longo": self.memoria.listar(user_id), "sessao": items,
                "janela": session.janela if session else {}}

    def _history(self, session_id):
        return self.session(session_id).history

    def chat(self, session_id, message, *, user_id="local", emit=None):
        session = self.session(session_id)
        with session.lock:
            session.emit, session.user_id = emit or Emissor(), user_id
            session.trim(self.llm)
            try:
                return self.chain.invoke({"session_id": session_id, "message": message},
                                         config={"configurable": {"session_id": session_id}})["response"]
            finally:
                session.emit = Emissor()

    def stream(self, session_id, message, *, user_id="local"):
        """Gerador de eventos SSE do turno: stage, token, memory e final."""
        def work(sink):
            from langchain_core.tracers.context import collect_runs

            with collect_runs() as collected:
                response = self.chat(session_id, message, user_id=user_id, emit=Emissor(sink))
                run = collected.traced_runs[0] if collected.traced_runs else None
            session = self.session(session_id)
            sink({"type": "final", "data": response.model_dump(), "trace_url": self._trace_url(run),
                  "memoria": session.ultimo, "janela": session.janela})
        return em_fila(work)

    def _trace_url(self, run):
        if not run or os.getenv("LANGSMITH_TRACING", "").lower() != "true" or not os.getenv("LANGSMITH_API_KEY"):
            return None
        try:
            from langsmith import Client

            return Client().get_run_url(run=run, project_name=os.getenv("LANGSMITH_PROJECT") or "default")
        except Exception:
            logger.warning("Link do LangSmith indisponível para este turno.")
            return None

    def _intent(self, message, session, memorias=()):
        if not self.llm:
            return interpretar(message)
        local = interpretar(message)
        try:
            parsed = self.llm.with_structured_output(Pedido).invoke(
                "Classifique a intenção e extraia apenas restrições explícitas do pedido em português. "
                "Use null para omissões. Se houver salário sem período, use mês. "
                "Converta ordinais em posição. Comparação com currículo é curriculo. "
                "Se o pedido só declara preferências ou fatos sobre o usuário, sem pedir busca, conversão, "
                "comparação nem consulta, a intenção é ajuda. Em cargo e stack, mantenha os termos do usuário. "
                "Em evitar_skills, liste só tecnologias que o usuário pediu para evitar, no pedido ou nas memórias. "
                f"Memórias do usuário: {[m['texto'] for m in memorias]}\n"
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

    def _reescrever(self, message, jobs):
        """Transformação de consulta: troca a pergunta pelo vocabulário das vagas em discussão."""
        if not jobs:
            return None
        if self.llm:
            try:
                listing = "; ".join(f"{j.title}: {j.description[:200]}" for j in jobs[:3])
                return self.llm.invoke(
                    "Reescreva a pergunta como uma consulta de busca para o currículo do candidato, usando os "
                    "cargos e as tecnologias das vagas. Responda só com a consulta, em uma linha.\n"
                    f"Pergunta: {message}\nVagas: {listing}").text.strip()[:240]
            except Exception:
                logger.warning("Reescrita por LLM indisponível; usando os termos das vagas.")
        terms = []
        for job in jobs[:3]:
            terms.extend([job.title, *skills_in(job.description)])
        return " ".join(dict.fromkeys(terms))

    def _redigir(self, message, draft, session, memories, emit):
        """Resposta final pela interface stream() da chain: tokens do LLM ou o rascunho verificado."""
        if not self.llm and any("curtas" in plain(p) for p in session.prefs):
            draft = draft.split("\n", 1)[0]
        pieces = []
        try:
            for piece in resposta_chain(self.llm).stream({
                    "pedido": message, "rascunho": draft,
                    "preferencias": "; ".join(session.prefs) or "nenhuma",
                    "memorias": "; ".join(m["texto"] for m in memories) or "nenhuma"}):
                pieces.append(piece)
                emit("token", text=piece)
        except Exception:
            logger.warning("Redação por LLM indisponível; usando o rascunho verificado.")
            rest = draft if not pieces else ""
            pieces = pieces or [draft]
            if rest:
                emit("token", text=rest)
        return "".join(pieces).strip() or draft

    def _turn(self, inputs):
        session_id, message = inputs["session_id"], inputs["message"]
        session = self.session(session_id)
        emit, user = session.emit, session.user_id
        traces, checks, cards, results, guardadas = [], [], [], {}, []

        # Demo mode has no model to decide what to keep, so local rules stand in for the tool.
        if not self.llm:
            longo, curto = extrair_por_regras(message)
            for tipo, texto in longo:
                if saved := self.memoria.guardar(user, tipo, texto, "regra local (modo demo)"):
                    guardadas.append(saved)
            for texto in curto:
                if texto not in session.prefs:
                    session.prefs.append(texto)
                    guardadas.append({"tipo": "nesta conversa", "texto": texto})
        usadas = self.memoria.buscar(user, message)

        emit.inicio("intencao", "OpenAI" if self.llm else "regras locais")
        router = RoteadorVagas(classificar=lambda text: self._intent(text, session, usadas))
        routed = router.invoke({"pedido": message})
        pedido, intent = routed["next_inputs"]["estruturado"], routed["destination"]
        query_text = plain(message)
        compare_search = (interpretar(message).intencao == "busca"
                          and bool(re.search(r"curriculo|compare|aderencia", query_text)))
        if compare_search:
            intent = "busca"
        if not self.llm and guardadas and not re.search(
                r"\b(?:busque|encontre|procure|liste|converta|compare|quais?)\b|mostre\s.*vagas", query_text):
            intent = "ajuda"  # the message only states preferences; nothing to search or convert
        if intent == "busca":
            updates = pedido.entidades.model_dump(exclude_none=True, exclude={"posicao"})
            if not updates.get("evitar_skills"):
                updates.pop("evitar_skills", None)
            session.entities = session.entities.model_copy(update=updates)
        target_pos = pedido.entidades.posicao or 1
        target = session.jobs.get(session.visible[target_pos - 1]) if target_pos <= len(session.visible) else None
        memories = session.retrieve(message)
        emit.fim("intencao", source="OpenAI" if self.llm else "regras locais", data={
            "pedido": {"intencao": intent, "entidades": pedido.entidades.model_dump(exclude_none=True, exclude_defaults=True)},
            "rota": intent, "rotas": ROTAS, "composicao": COMPOSICAO[intent],
            "classificador": "with_structured_output(Pedido) no LLM" if self.llm else "regras locais (modo demo)",
            "referencia": (f"posição {pedido.entidades.posicao} da última lista → {target.title} · {target.company}"
                           if pedido.entidades.posicao and target else None),
            "turno": len(session.history.messages) // 2 + 1})

        def log(name, start, status, detail, source=""):
            traces.append(ToolCall(name=name, status=status, detail=detail, source=source,
                                   duration_ms=round((monotonic() - start) * 1000)))
            logger.info("tool=%s source=%s status=%s", name, source, status)

        @tool
        def buscar_vagas() -> list:
            """Busca vagas reais ou simuladas segundo os filtros desta sessão."""
            if "jobs" not in results:
                terms = session.entities.stack or session.entities.cargo or ""
                jobs, calls = self.providers.buscar(terms, emit)
                if terms and not jobs and self.llm and not any(c.status == "erro" for c in calls):
                    # Retrieval failure: a Portuguese query finds nothing in English ads. Rewrite and retry.
                    try:
                        rewritten = termos_em_ingles(terms, self.llm)
                    except Exception:
                        rewritten = ""
                    if rewritten and plain(rewritten) != plain(terms):
                        jobs, calls = self.providers.buscar(rewritten, emit, nota={"reescrita": {
                            "antesQ": terms, "antes": 0, "depoisQ": rewritten,
                            "diag": "a consulta em português não casou com nenhum anúncio em inglês; "
                                    "o LLM traduziu os termos e a busca foi refeita."}})
                        results["reescrita"] = f'A busca por "{terms}" não trouxe anúncios; refiz com "{rewritten}".'
                self.repo.save(jobs)
                traces.extend(calls)
                for call in calls:
                    logger.info("tool=%s source=%s status=%s", call.name, call.source, call.status)
                results["jobs"] = jobs
            return [j.model_dump(include={"id", "title", "location", "description"}) |
                    {"description": j.description[:600]} for j in results["jobs"][:12]]

        def cotar(currency):
            """One quote per currency per turn; emits the exchange stage."""
            if currency not in results.setdefault("rates", {}):
                emit.inicio("cambio", "AwesomeAPI")
                try:
                    rate, date, source = self.providers.cotacao(currency)
                except Exception:
                    emit.fim("cambio", "erro", source="AwesomeAPI", detail="O câmbio está indisponível.")
                    raise
                results["rates"][currency] = rate, date, source
                emit.fim("cambio", "dummy" if self.dummy else "ok", source="AwesomeAPI",
                         detail=f"1 {currency} = R$ {rate}", data={
                             "par": f"{currency}-BRL", "taxa": str(rate), "data": date, "fonte": source,
                             "url": None if self.dummy else f"https://economia.awesomeapi.com.br/json/last/{currency}-BRL"})
            return results["rates"][currency]

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
                    rate, date, source = cotar(pay.currency)
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
            if "rates" not in results:
                emit.inicio("cambio", "AwesomeAPI")
                emit.fim("cambio", "incerto", source="AwesomeAPI", detail=answer)
            log("converter_moeda", start, "incerto", answer)
            results["conversion"] = answer
            return answer

        @tool
        def recuperar_contexto() -> list:
            """Recupera do índice documental os trechos do currículo que ajudam neste pedido."""
            if "context" in results:
                return results["context"]
            start = monotonic()
            emit.inicio("curriculo", "FAISS documental")
            search = lambda q: retrieve(q, kind="curriculo", index_path=self.index_path, real=not self.dummy)
            recovery = None
            try:
                matches = search(message)
                # A question such as "qual combina mais?" shares no vocabulary with the résumé.
                if matches and matches[0]["score"] < LIMIAR_RECUPERACAO:
                    jobs = [session.jobs[i] for i in session.visible if i in session.jobs] or results.get("jobs", [])
                    rewritten = self._reescrever(message, jobs)
                    again = search(rewritten) if rewritten else None
                    if again and again[0]["score"] > matches[0]["score"]:
                        brief = lambda rows: [{"s": r["score"], "t": r["trecho"][:140]} for r in rows]
                        recovery = {"antesQ": message, "antes": brief(matches), "depoisQ": rewritten,
                                    "depois": brief(again), "limiar": LIMIAR_RECUPERACAO,
                                    "tecnica": "reescrita da consulta" + (" pelo LLM" if self.llm else " com os termos das vagas"),
                                    "diag": (f"a melhor similaridade da pergunta original foi {matches[0]['score']:.2f}, abaixo do "
                                             f"limiar {LIMIAR_RECUPERACAO:.2f}: a pergunta não usa o vocabulário do currículo.")}
                        matches = again
            except Exception:
                matches = None
            status = "ok" if matches else "indisponível"
            log("recuperar_contexto", start, status,
                matches[0]["trecho"][:700] if matches else "Índice documental indisponível. Execute o notebook 01.",
                "FAISS documental")
            emit.fim("curriculo", "ok" if matches else "erro", source="FAISS documental",
                     detail=f"{len(matches)} trecho(s) recuperado(s)." if matches else "Índice documental indisponível.",
                     data={"trechos": [{"s": m["score"], "t": m["trecho"][:160]} for m in matches or []],
                           "indice": self.index_path.name, "k": 3, "rec": recovery,
                           "embeddings": "text-embedding-3-small" if not self.dummy else "MiniLM multilíngue local"})
            results["context"] = matches or []
            return results["context"]

        @tool
        def consultar_candidaturas() -> list:
            """Consulta as vagas e as candidaturas desta sessão em modo somente leitura."""
            if "rows" in results:
                return results["rows"]
            start = monotonic()
            emit.inicio("historico", "SQLite")
            query = None
            try:
                query, rows = self._sql(message, session_id)
                log("consultar_candidaturas", start, "ok", f"{query} | {len(rows)} linha(s).", "SQLite")
            except Exception as exc:
                logger.warning("Consulta indisponível: %s", type(exc).__name__)
                rows = []
                log("consultar_candidaturas", start, "erro", "Não foi possível executar a consulta.", "SQLite")
            emit.fim("historico", "ok" if query else "erro", source="SQLite",
                     detail=f"{len(rows)} linha(s)." if query else "Não foi possível executar a consulta.",
                     data={"sql": query, "linhas": rows[:5], "n": len(rows),
                           "gerador": "create_sql_query_chain (LLM)" if self.llm else "regras locais (modo demo)"})
            results["rows"] = rows
            return rows

        @tool
        def guardar_memoria(escopo: Literal["longo", "conversa"],
                            tipo: Literal["semântica", "episódica", "procedural"], texto: str) -> str:
            """Guarda um fato ou preferência do usuário. escopo "longo" vale para conversas futuras;
            "conversa" vale só para esta. texto: uma frase curta em português, em terceira pessoa."""
            if escopo == "conversa":
                if texto not in session.prefs:
                    session.prefs.append(texto[:240])
                    guardadas.append({"tipo": "nesta conversa", "texto": texto[:240]})
                return "Preferência guardada para esta conversa."
            if saved := self.memoria.guardar(user, tipo, texto, "LLM · ferramenta guardar_memoria"):
                guardadas.append(saved)
                return "Memória de longo prazo guardada."
            return "Essa memória já existia."

        routes = {"busca": buscar_vagas, "cambio": converter_moeda, "curriculo": recuperar_contexto,
                  "carta": recuperar_contexto, "candidaturas": consultar_candidaturas}
        preliminary = {}
        selected = routes.get(intent)
        extra = (recuperar_contexto.name,) if compare_search else ()
        emit.inicio("ferramentas", "OpenAI" if self.llm else "modelo roteirizado")
        decision = {"t0": monotonic(), "ms": None}
        calls = ToolLog()

        class Decisao(BaseCallbackHandler):
            """The model's choice ends when the first tool starts."""
            def on_tool_start(inner, serialized, input_str, **kwargs):
                if decision["ms"] is None:
                    decision["ms"] = round((monotonic() - decision["t0"]) * 1000)
                    emit.fim("ferramentas", source="OpenAI" if self.llm else "modelo roteirizado",
                             duration_ms=decision["ms"])

        if selected or self.llm:
            domain = list({route.name: route for route in routes.values()}.values())
            executor = make_executor(self.llm or scripted_model(selected.name, also=extra), [*domain, guardar_memoria])
            try:
                actions = ", ".join((selected.name, *extra)) if selected else "nenhuma ferramenta de domínio"
                proposal = executor.invoke({"input": f"Intenção: {intent}. Use estas ferramentas: {actions}. "
                                            f"Pedido: {message}\nResumo: {session.summary}\nMemória: {memories}\n"
                                            f"Memórias de longo prazo já guardadas: {[m['texto'] for m in usadas]}",
                                            "chat_history": inputs["chat_history"]},
                                           config={"callbacks": [calls, Decisao()]})
                if intent == "busca":
                    preliminary = {c.job_id: c.claim[:280] for c in Draft.model_validate(
                        JsonOutputParser().parse(output_text(proposal["output"]))).claims[:12]}
            except Exception:
                logger.warning("Proposta do agente indisponível; usando percurso determinístico.")
        if decision["ms"] is None:
            decision["ms"] = round((monotonic() - decision["t0"]) * 1000)
        tokens = [e["tokens"] for e in calls.events if e["evento"] == "modelo" and e["tokens"]]
        ensured_tools = [t.name for t, key in ((selected, {"busca": "jobs", "cambio": "conversion",
                          "curriculo": "context", "carta": "context", "candidaturas": "rows"}.get(intent)),
                          (recuperar_contexto if compare_search else None, "context"))
                         if t is not None and key not in results]
        emit("stage", key="ferramentas", status="ok", source="OpenAI" if self.llm else "modelo roteirizado",
             duration_ms=decision["ms"], detail="", data={
                 "executor": "create_openai_tools_agent + AgentExecutor (max_iterations=4)",
                 "modelo": getattr(self.llm, "model_name", None) or "roteirizado, sem LLM",
                 "disponiveis": [t.name for t in (*{r.name: r for r in routes.values()}.values(), guardar_memoria)],
                 "chamadas": [e for e in calls.events if e["evento"] in {"action", "observation", "erro"}],
                 "tokens": tokens, "prompt": AGENT_SYSTEM, "callbacks": len(calls.events),
                 "fallback": ensured_tools})
        if selected:
            # Tool calls are idempotent within a turn. Fill the required result if the model skipped it.
            selected.invoke({})
            if compare_search:
                recuperar_contexto.invoke({})
        if guardadas:
            usadas = self.memoria.buscar(user, message)  # include what was stored during this turn
        evitar = list(dict.fromkeys([*session.entities.evitar_skills, *skills_evitadas(usadas)]))
        em_reais = any(re.search(r"salario.*(?:r\$|reais|brl)", plain(m["texto"])) for m in usadas)

        if intent == "busca":
            jobs = results["jobs"]
            ranked = []
            discarded, pending = 0, 0
            entities = session.entities.model_copy(update={"evitar_skills": evitar})
            fits = avaliar_fit.batch([(self.profile, f"{job.title} {job.description}") for job in jobs])
            for job, fit in zip(jobs, fits):
                verdict, evidence, reason = restrictions(job, entities, self.profile)
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
            emit.inicio("verificacao", "NLI local")
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
                if pay and em_reais and pay.currency != "BRL" and verdict != "descartado":
                    start = monotonic()
                    try:
                        rate, date, source = cotar(pay.currency)
                        salary += f" · ≈ R$ {pay.low * rate:,.2f}"
                        if not any(t.name == "converter_moeda" and pay.currency in t.detail for t in traces):
                            log("converter_moeda", start, "dummy" if self.dummy else "ok",
                                f"1 {pay.currency} = R$ {rate}. {source}. Aplicado pela memória procedural.", source)
                    except Exception:
                        logger.warning("Câmbio indisponível para aplicar a preferência de moeda.")
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
            avoided = [c for c in cards if "Você pediu para evitar" in c.reason]
            if avoided:
                lines.append(f"Deixei de fora {len(avoided)} vaga(s) por causa da sua preferência guardada: evitar {', '.join(evitar)}.")
            if results.get("reescrita"):
                lines.append(results["reescrita"])
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
            if guardadas:
                answer = "Anotei suas preferências. " + answer

        response = ChatOut(answer=answer, recommendations=cards, tool_calls=traces, verification=checks,
                           mode="dummy" if self.dummy else "real")
        if response.verification:
            counts = {}
            for check in response.verification:
                counts[check.status] = counts.get(check.status, 0) + 1
            by_nli = [c for c in response.verification if c.nli_label]
            if intent != "busca":
                emit.inicio("verificacao", "regra de evidência")
            emit.fim("verificacao", "incerto" if counts.get("incerta") else "ok",
                     source="NLI local" if intent == "busca" else "regra de evidência",
                     detail=f"{len(response.verification)} afirmação(ões) checada(s).", data={
                         "contagem": counts, "total": len(response.verification),
                         "nli": [{"job_id": c.job_id, "rotulo": c.nli_label, "score": c.nli_score,
                                  "status": c.status, "claim": c.claim} for c in by_nli],
                         "modelo": NLI_MODEL if by_nli else None,
                         "logica": "checagem de coerência pelo LLM" if self.llm else None,
                         "corrigidas": [c.job_id for c in response.verification if "Correção aplicada" in c.reason]})

        emit.inicio("resposta", "OpenAI" if self.llm else "rascunho verificado")
        final = self._redigir(message, answer, session, usadas, emit)
        response.answer = final
        parts = {"sistema": AGENT_SYSTEM, "resumo": session.summary,
                 "buffer": "\n".join(m.text for m in session.mensagens()),
                 "memoria_longa": "\n".join(m["texto"] for m in usadas),
                 "ferramentas": "\n".join(t.detail for t in traces)}
        counted = {name: contar_tokens(text) for name, text in parts.items()}
        session.janela = {
            "tokens": counted, "total": sum(v or 0 for v in counted.values()) if None not in counted.values() else None,
            "tokenizador": "o200k_base", "mensagens": len(session.history.messages) + 2, "limite_mensagens": 8,
            "resumiu": bool(session.summary), "buffer": "ConversationBufferMemory", "session_id": session_id}
        session.ultimo = {"usadas": usadas, "guardadas": guardadas, "sessao": list(session.prefs), "evitar": evitar}
        emit("memory", **session.ultimo)
        emit.fim("resposta", source="OpenAI" if self.llm else "rascunho verificado", data={
            "session_id": session_id, "mensagens": session.janela["mensagens"], "janela": session.janela,
            "historico": "RunnableWithMessageHistory por session_id",
            "stream": "resposta_chain.stream()", "memoria": session.ultimo})
        return {"response": response, "history_answer": final}
