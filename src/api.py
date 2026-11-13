import logging
from functools import lru_cache
from os import getenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .agente import Radar
from .config import ROOT, dummy_mode
from .models import CandidaturaIn, ChatIn, ChatOut

logging.getLogger("src.agente").setLevel(logging.INFO)
logging.getLogger("src.agente").addHandler(logging.StreamHandler())

app = FastAPI(title="Radar Remoto")
if origin := getenv("CORS_ORIGIN"):
    app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["POST"], allow_headers=["Content-Type"])


@lru_cache(maxsize=1)
def get_radar():
    return Radar(dummy=dummy_mode())


@app.get("/", include_in_schema=False)
def home():
    path = ROOT / "web" / "index.html"
    if not path.exists():
        raise HTTPException(503, "A exportação do Claude Design ainda não foi instalada. Use /docs para testar a API.")
    return FileResponse(path, media_type="text/html")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "dummy" if dummy_mode() else "real"}


@app.post("/chat", response_model=ChatOut)
def chat(request: ChatIn):
    try:
        return get_radar().chat(request.session_id, request.message)
    except RuntimeError as exc:
        if str(exc).startswith("Configure OPENAI_"):
            raise HTTPException(503, str(exc)) from exc
        raise


@app.post("/candidaturas", response_model=CandidaturaIn)
def register_application(request: CandidaturaIn):
    """Registra uma ação já tomada pelo candidato; não envia candidaturas."""
    try:
        get_radar().record_application(request.session_id, request.vaga_id, request.status)
    except KeyError as exc:
        raise HTTPException(404, "Busque a vaga nesta sessão antes de registrar a candidatura.") from exc
    return request
