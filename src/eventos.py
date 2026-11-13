"""Eventos de etapa do turno: alimentam o SSE de /chat/stream e a linha do tempo da interface."""
import json
from functools import lru_cache
from queue import Queue
from threading import Thread
from time import monotonic
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler


class Emissor:
    """Recebe os eventos do turno. Sem destino (chat síncrono, testes), descarta tudo."""

    def __init__(self, sink=None):
        self.sink = sink
        self._inicio = {}

    def __call__(self, tipo, **payload):
        if self.sink:
            self.sink({"type": tipo, **payload})

    def inicio(self, key, source=""):
        self._inicio[key] = monotonic()
        self("stage", key=key, status="running", source=source)

    def fim(self, key, status="ok", *, source="", detail="", data=None, duration_ms=None):
        start = self._inicio.pop(key, None)
        if duration_ms is None and start is not None:
            duration_ms = round((monotonic() - start) * 1000)
        self("stage", key=key, status=status, source=source, detail=detail, data=data or {},
             duration_ms=duration_ms)


class ToolLog(BaseCallbackHandler):
    """Callback de logging: registra cada ação, observação e uso de tokens do executor."""

    def __init__(self):
        self.events, self.start = [], {}

    def on_tool_start(self, serialized, input_str, *, run_id: UUID, **kwargs):
        self.start[run_id] = (serialized["name"], monotonic())
        self.events.append({"evento": "action", "tool": serialized["name"], "input": input_str})

    def on_tool_end(self, output, *, run_id: UUID, **kwargs):
        name, start = self.start.pop(run_id)
        self.events.append({"evento": "observation", "tool": name, "duration_ms": round((monotonic() - start)*1000),
                            "output": str(getattr(output, "content", output))[:250]})

    def on_tool_error(self, error, *, run_id: UUID, **kwargs):
        name, start = self.start.pop(run_id, ("?", monotonic()))
        self.events.append({"evento": "erro", "tool": name, "output": type(error).__name__})

    def on_llm_end(self, response, **kwargs):
        output = response.llm_output or {}
        usage = output.get("token_usage") or output.get("usage")
        if not usage:
            usage = next((getattr(getattr(g, "message", None), "usage_metadata", None)
                          for row in response.generations for g in row
                          if getattr(getattr(g, "message", None), "usage_metadata", None)), None)
        self.events.append({"evento": "modelo", "tokens": usage})


@lru_cache(maxsize=1)
def _encoding():
    import tiktoken

    return tiktoken.get_encoding("o200k_base")


def contar_tokens(text):
    """Contagem real com o tokenizador o200k_base; None se o tiktoken não estiver disponível."""
    try:
        return len(_encoding().encode(str(text or "")))
    except Exception:
        return None


def sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"


def em_fila(work):
    """Roda `work(sink)` numa thread e entrega os eventos conforme chegam."""
    queue, done = Queue(), object()

    def run():
        try:
            work(queue.put)
        except Exception as exc:  # the stream must always end with a readable event
            message = str(exc) if isinstance(exc, (RuntimeError, ValueError)) else type(exc).__name__
            queue.put({"type": "error", "message": message})
        finally:
            queue.put(done)

    Thread(target=run, daemon=True).start()
    while (event := queue.get()) is not done:
        yield sse(event)
