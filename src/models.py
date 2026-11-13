from typing import Literal

from pydantic import BaseModel, Field


class PerfilCandidato(BaseModel):
    skills: list[str] = Field(default_factory=list)
    senioridade: str | None = None
    cargos_alvo: list[str] = Field(default_factory=list)
    ingles: str | None = None
    pretensao_salarial: str | None = None


class Vaga(BaseModel):
    id: str
    title: str
    company: str
    source: str
    url: str
    description: str
    location: str = ""
    salary_hint: str = ""


class Entidades(BaseModel):
    cargo: str | None = None
    stack: str | None = None
    salario_min: float | None = None
    moeda: Literal["USD", "EUR", "BRL"] | None = None
    periodo: Literal["month", "year"] | None = None
    fuso: int | None = None
    aceita_brasil: bool | None = None
    ingles: str | None = None
    posicao: int | None = None


class Pedido(BaseModel):
    intencao: Literal["busca", "cambio", "curriculo", "carta", "candidaturas", "ajuda"]
    entidades: Entidades = Field(default_factory=Entidades)


class SessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")


class ChatIn(SessionRequest):
    message: str = Field(min_length=1, max_length=3000, pattern=r"\S")


class Recomendacao(BaseModel):
    id: str
    title: str
    company: str
    source: str
    url: str
    status: Literal["recomendado", "pendente", "descartado"]
    reason: str
    evidence: str
    skills: list[str]
    salary: str | None = None


class ToolCall(BaseModel):
    name: str
    status: str
    detail: str
    duration_ms: int
    source: str = ""


class Verificacao(BaseModel):
    job_id: str
    claim: str
    status: Literal["confirmada", "contradita", "incerta", "indisponível"]
    evidence: str
    reason: str


class ChatOut(BaseModel):
    answer: str
    recommendations: list[Recomendacao] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    verification: list[Verificacao] = Field(default_factory=list)
    mode: Literal["dummy", "real"]


class CandidaturaIn(SessionRequest):
    vaga_id: str = Field(min_length=1, max_length=180)
    status: Literal["salva", "enviada", "descartada"]
