from typing import Any

from langchain_classic.chains.router.base import RouterChain

from .rules import interpretar

ROTAS = {
    "busca": "busca de vagas",
    "cambio": "conversão de moeda",
    "curriculo": "análise de currículo",
    "carta": "carta de apresentação",
    "candidaturas": "histórico de candidaturas",
    "ajuda": "ajuda",
}


class RoteadorVagas(RouterChain):
    """RouterChain do domínio: classifica o pedido e devolve o destino do turno.

    `classificar` recebe o texto e devolve um `Pedido`. O padrão são as regras locais;
    no modo real o agente injeta a classificação por saída estruturada do LLM.
    """

    classificar: Any = None

    @property
    def input_keys(self):
        return ["pedido"]

    def _call(self, inputs, run_manager=None):
        pedido = (self.classificar or interpretar)(inputs["pedido"])
        return {"destination": pedido.intencao,
                "next_inputs": {"pedido": inputs["pedido"], "estruturado": pedido}}
