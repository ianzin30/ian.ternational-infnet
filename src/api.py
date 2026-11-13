import json
import logging
import os
import re
from threading import Lock

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agente import CurriculoInvalido, Radar
from .config import ROOT, dummy_mode
from .eventos import Emissor, em_fila
from .models import CandidaturaIn, ChatIn, ChatOut, ModeloIn, ReactIn

logging.getLogger("src.agente").setLevel(logging.INFO)
logging.getLogger("src.agente").addHandler(logging.StreamHandler())

app = FastAPI(title="ian.ternational")
if origin := os.getenv("CORS_ORIGIN"):
    app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST", "DELETE"],
                       allow_headers=["Content-Type"])

DIST = ROOT / "web" / "dist"
SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
USER = Query(default="local", min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
MAX_PDF = 5 * 1024 * 1024
_state = {"radar": None}
_lock = Lock()


def get_radar():
    with _lock:
        if _state["radar"] is None:
            _state["radar"] = Radar(dummy=dummy_mode())
        return _state["radar"]


def real_available():
    """(pode usar o modo real?, motivo quando não pode)"""
    if not os.getenv("OPENAI_MODEL") or not os.getenv("OPENAI_API_KEY"):
        return False, "Configure OPENAI_MODEL e OPENAI_API_KEY no .env."
    return True, ""


def model_label(model_id):
    return " ".join(part.upper() if part.lower() == "gpt" or re.fullmatch(r"\d[\w.]*", part) else part.capitalize()
                    for part in model_id.split("-")).replace("GPT ", "GPT-", 1)


def models_payload():
    radar = get_radar()
    real_id = os.getenv("OPENAI_MODEL") or "modelo-real"
    available, reason = real_available()
    return {"ativo": "demo" if radar.dummy else real_id, "modo": "dummy" if radar.dummy else "real", "opcoes": [
        {"id": real_id, "rotulo": model_label(real_id), "descricao": "OpenAI · modo real",
         "disponivel": available, "motivo": reason},
        {"id": "demo", "rotulo": "Demo roteirizado", "descricao": "Sem custo · dados fictícios",
         "disponivel": True, "motivo": ""}]}


@app.get("/", include_in_schema=False)
def home():
    path = DIST / "index.html"
    if not path.exists():
        raise HTTPException(503, "A interface ainda não foi compilada. Rode `npm --prefix web run build` "
                                 "ou use /docs para testar a API.")
    return FileResponse(path, media_type="text/html", headers={"Cache-Control": "no-cache"})


@app.get("/health")
def health():
    radar = _state["radar"]
    return {"status": "ok", "mode": "dummy" if (radar.dummy if radar else dummy_mode()) else "real"}


@app.post("/chat", response_model=ChatOut)
def chat(request: ChatIn):
    try:
        return get_radar().chat(request.session_id, request.message, user_id=request.user_id)
    except RuntimeError as exc:
        if str(exc).startswith("Configure OPENAI_"):
            raise HTTPException(503, str(exc)) from exc
        raise


@app.post("/chat/stream")
def chat_stream(request: ChatIn):
    """Server-Sent Events do turno: `stage` (etapas), `token` (resposta), `memory` e `final`."""
    radar = get_radar()
    return StreamingResponse(radar.stream(request.session_id, request.message, user_id=request.user_id),
                             media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/react")
def react(request: ReactIn):
    """Roda o mesmo pedido no ReAct clássico (initialize_agent, ZERO_SHOT_REACT_DESCRIPTION)."""
    from .demo import react_demo

    radar = get_radar()
    try:
        result = react_demo(live=not radar.dummy, pergunta=request.message, llm=radar.llm)
    except Exception as exc:
        raise HTTPException(502, f"O agente ReAct não concluiu ({type(exc).__name__}).") from exc
    return {key: result[key] for key in ("modelo", "resposta", "ciclo", "callbacks", "memoria", "fontes_ao_vivo")}


@app.post("/candidaturas", response_model=CandidaturaIn, response_model_exclude_unset=True)
def register_application(request: CandidaturaIn):
    """Registra uma ação já tomada pelo candidato; não envia candidaturas."""
    try:
        get_radar().record_application(request.session_id, request.vaga_id, request.status, request.user_id)
    except KeyError as exc:
        raise HTTPException(404, "Busque a vaga nesta sessão antes de registrar a candidatura.") from exc
    return request


# ---- memória e sessões --------------------------------------------------------------------
@app.get("/memoria")
def memory(user_id: str = USER, session_id: str | None = Query(default=None, max_length=80)):
    return get_radar().memoria_view(user_id, session_id)


@app.delete("/memoria/{memoria_id}")
def forget(memoria_id: int, user_id: str = USER):
    if not get_radar().memoria.esquecer(user_id, memoria_id):
        raise HTTPException(404, "Memória não encontrada.")
    return {"ok": True}


@app.delete("/sessoes/{session_id}")
def close_session(session_id: str):
    return {"ok": get_radar().fechar_sessao(session_id)}


# ---- currículo ----------------------------------------------------------------------------
@app.get("/curriculo")
def resume():
    path = get_radar().arquivo_curriculo()
    if not path.exists():
        raise HTTPException(404, "O PDF do currículo não foi gerado. Rode scripts.setup_assets.")
    return FileResponse(path, media_type="application/pdf", headers={"Cache-Control": "no-store"})


@app.get("/curriculo/info")
def resume_info():
    return get_radar().info_curriculo()


@app.post("/curriculo")
def upload_resume(arquivo: UploadFile = File(...)):
    """Troca o currículo. Responde em SSE com as etapas: enviando, lendo, indexando, extraindo."""
    name = (arquivo.filename or "curriculo.pdf")[:120]
    content = arquivo.file.read(MAX_PDF + 1)
    if len(content) > MAX_PDF:
        raise HTTPException(413, "O arquivo passa de 5 MB.")
    if arquivo.content_type not in {"application/pdf", "application/x-pdf"} or not content.startswith(b"%PDF"):
        raise HTTPException(415, "Envie um arquivo PDF.")
    radar = get_radar()

    def work(sink):
        emit = Emissor(sink)
        emit.inicio("enviando", "FastAPI")
        emit.fim("enviando", source="FastAPI", data={"bytes": len(content)})
        try:
            info = radar.enviar_curriculo(content, name, emit)
        except CurriculoInvalido:
            sink({"type": "error", "erro": "sem-texto",
                  "message": "Não encontrei texto neste PDF. Ele parece digitalizado; envie um PDF com texto selecionável."})
            return
        sink({"type": "final", "data": info})

    return StreamingResponse(em_fila(work), media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/curriculo/reset")
def reset_resume():
    return get_radar().restaurar_curriculo()


# ---- modelos ------------------------------------------------------------------------------
@app.get("/modelos")
def models():
    return models_payload()


@app.post("/modelo")
def switch_model(request: ModeloIn):
    """Troca entre o modelo real e o demo roteirizado. Recria o agente: as sessões recomeçam."""
    dummy = request.id == "demo"
    if not dummy:
        available, reason = real_available()
        if not available:
            raise HTTPException(409, reason)
        if request.id != os.getenv("OPENAI_MODEL"):
            raise HTTPException(404, "Modelo desconhecido.")
    with _lock:
        current = _state["radar"]
        if current is None or current.dummy != dummy:
            _state["radar"] = Radar(dummy=dummy)
    return models_payload()


# ---- avaliação ----------------------------------------------------------------------------
@app.get("/avaliacao")
def evaluation():
    """Métricas do último experimento publicado no LangSmith por scripts.evaluate --langsmith."""
    path = ROOT / "output" / "langsmith.json"
    if not path.exists():
        return {"disponivel": False}
    return {"disponivel": True, **json.loads(path.read_text())}


if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{arquivo}", include_in_schema=False)
def static_root(arquivo: str):
    """Ícones e demais arquivos na raiz do build."""
    path = (DIST / arquivo).resolve()
    if path.parent != DIST.resolve() or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)
