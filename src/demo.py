import os
from time import monotonic
from uuid import UUID

from langchain_classic.agents import AgentType, initialize_agent
from langchain_classic.chains.router.base import RouterChain
from langchain_classic.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain_classic.output_parsers import OutputFixingParser
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, chain
from langchain_core.tools import Tool, tool

from .config import DATA, live_model
from .agente import output_text
from .executor import make_executor, scripted_model
from .prompts import AGENT_SYSTEM, avaliar_fit, perfil_local, resumo_chain
from .rag import retrieve
from .repository import fixtures
from .rules import interpretar
from .tools import Providers

QUESTIONS = (
    "Mostre vagas remotas de Python",
    "Só as que aceitam Brasil",
    "Converta o salário da segunda",
    "Qual combina mais com meu currículo?",
)


class RoteadorVagas(RouterChain):
    @property
    def input_keys(self):
        return ["pedido"]

    def _call(self, inputs, run_manager=None):
        pedido = interpretar(inputs["pedido"])
        return {"destination": pedido.intencao, "next_inputs": {"pedido": inputs["pedido"]}}


class ToolLog(BaseCallbackHandler):
    def __init__(self):
        self.events, self.start = [], {}

    def on_tool_start(self, serialized, input_str, *, run_id: UUID, **kwargs):
        self.start[run_id] = (serialized["name"], monotonic())
        self.events.append({"evento": "action", "tool": serialized["name"], "input": input_str})

    def on_tool_end(self, output, *, run_id: UUID, **kwargs):
        name, start = self.start.pop(run_id)
        self.events.append({"evento": "observation", "tool": name, "duration_ms": round((monotonic() - start)*1000),
                            "output": str(output)[:250]})

    def on_llm_end(self, response, **kwargs):
        output = response.llm_output or {}
        usage = output.get("token_usage") or output.get("usage")
        if not usage:
            usage = next((getattr(getattr(g, "message", None), "usage_metadata", None)
                          for row in response.generations for g in row
                          if getattr(getattr(g, "message", None), "usage_metadata", None)), None)
        self.events.append({"evento": "modelo", "tokens": usage})


def _no_key_llm(outputs):
    return FakeListLLM(responses=outputs, custom_get_token_ids=lambda value: list(range(len(value.split()))))


def react_demo(*, live=False):
    providers = Providers(not live, fixtures(DATA))
    trace = ToolLog()
    llm = live_model() if os.getenv("NOTEBOOK_OPENAI") == "1" else _no_key_llm([
        "Thought: Preciso de anúncios da stack solicitada.\nAction: buscar_vagas\nAction Input: Python",
        "Thought: A busca devolveu anúncios.\nFinal Answer: Consulte a observação para ver as vagas.",
    ])
    memory = ConversationSummaryBufferMemory(llm=llm, memory_key="chat_history",
                                              output_key="output", max_token_limit=120)
    def search(stack):
        jobs, calls = providers.buscar(stack)
        return str({"vagas": [{"titulo": j.title, "fonte": j.source, "url": j.url} for j in jobs[:2]],
                    "fontes": [{"origem": c.source, "status": c.status} for c in calls]})
    def convert(currency):
        rate, date, source = providers.cotacao(currency.strip().upper())
        return f"{rate} BRL, {date}, {source}"
    tools = [Tool(name="buscar_vagas", func=search, description="Busca vagas por stack"),
             Tool(name="converter_moeda", func=convert, description="Consulta USD ou EUR em BRL")]
    agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                             memory=memory, return_intermediate_steps=True)
    output = agent.invoke({"input": "Busque vagas remotas de Python."}, config={"callbacks": [trace]})
    return {"modelo": "roteirizado" if isinstance(llm, FakeListLLM) else "OpenAI",
            "fontes_ao_vivo": live, "resposta": output_text(output["output"]),
            "decisao": "Consultar o catálogo pela stack Python.",
            "passos": [(act.tool, str(obs)) for act, obs in output["intermediate_steps"]],
            "callbacks": trace.events, "memoria": memory.buffer}


def composicao():
    providers = Providers(True, fixtures(DATA))
    parallel = RunnableParallel(remotive=RunnableLambda(lambda _: len(providers.remotive()[0])),
                                arbeitnow=RunnableLambda(lambda _: len(providers.arbeitnow()[0])))
    profile = perfil_local((DATA / "curriculo.txt").read_text())
    sequential = resumo_chain() | RunnableLambda(lambda text: avaliar_fit.invoke((profile, text)))
    router = RoteadorVagas()
    return {"sequencial": sequential.invoke({"vaga": providers.fixtures[0].description}),
            "paralela": parallel.invoke(None),
            "router": [router.invoke({"pedido": q})["destination"] for q in (
                QUESTIONS[0], QUESTIONS[3], "Escreva uma carta", "Minhas candidaturas")]}


@chain
def perfil_imperativo(text):
    from .prompts import perfil_chain
    if not text.strip():
        from .models import PerfilCandidato
        return PerfilCandidato()
    return perfil_chain().invoke({"curriculo": text})


def reliability_demo():
    parser = OutputFixingParser.from_llm(_no_key_llm(['{"aceita_brasil": null}']), JsonOutputParser(), max_retries=1)
    return {"parser_corrigido": parser.parse("saída inválida"), "faiss": retrieve("currículo de Python", 1, kind="curriculo")}


def buffer_demo():
    memory = ConversationBufferMemory()
    memory.save_context({"input": QUESTIONS[0]}, {"output": "Encontrei vagas de Python."})
    memory.save_context({"input": QUESTIONS[1]}, {"output": "Mantive o cargo Python e apliquei Brasil."})
    return memory.load_memory_variables({})


def provider_function_call(*, live):
    providers = Providers(not live, fixtures(DATA))

    @tool
    def consultar_apis(stack: str) -> dict:
        """Busca vagas por stack nos provedores e consulta uma cotação USD–BRL."""
        jobs, trace = providers.buscar(stack)
        result = {"vagas": [{"titulo": j.title, "fonte": j.source, "url": j.url} for j in jobs[:3]],
                  "fontes": [t.model_dump() for t in trace]}
        for currency in ("USD", "EUR"):
            try:
                quote, date, source = providers.cotacao(currency)
                result[currency] = {"taxa": str(quote), "data": date, "fonte": source}
            except Exception as exc:
                result[currency] = {"erro": type(exc).__name__}
        return result

    model_live = os.getenv("NOTEBOOK_OPENAI") == "1"
    model = live_model() if model_live else scripted_model(consultar_apis.name, {"stack": "Python"})
    trace = ToolLog()
    run = make_executor(model, [consultar_apis]).invoke({"input": "Use consultar_apis para buscar Python e câmbio."},
                                                        config={"callbacks": [trace]})
    return {"modelo": "OpenAI" if model_live else "roteirizado", "http_real": live,
            "observacao": [obs for _, obs in run["intermediate_steps"]], "callbacks": trace.events}


def recovery_demo():
    from .rag import rewrite_job_query

    @tool
    def buscar_no_indice(consulta: str) -> list:
        """Recupera dois trechos de vagas do índice FAISS documental existente."""
        return retrieve(consulta, 2, kind="vaga") or []

    query = "desenvolvedor backend sênior"
    rewritten = rewrite_job_query(query)
    def run(q):
        model = scripted_model(buscar_no_indice.name, {"consulta": q})
        execution = make_executor(model, [buscar_no_indice]).invoke({"input": q})
        return execution["intermediate_steps"][0][1]

    return {"consulta_original": query, "reescrita": rewritten,
            "esperado": "demo-aurora", "antes": run(query), "depois": run(rewritten)}
