import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
load_dotenv(ROOT / ".env")
if not os.getenv("LANGSMITH_API_KEY"):
    # Tracing without a key only produces 401 noise; keep it off until the key is set.
    os.environ["LANGSMITH_TRACING"] = "false"


def dummy_mode():
    return os.getenv("MODO_DUMMY", "true").lower() in {"1", "true", "yes"}


def live_model():
    from langchain_openai import ChatOpenAI

    model = os.getenv("OPENAI_MODEL")
    if not model or not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Configure OPENAI_MODEL e OPENAI_API_KEY para usar o modo real.")
    from langchain_core.outputs import ChatGeneration, ChatResult

    def cut(text, stop):
        ends = [text.find(s) for s in stop if s in text]
        return text[:min(ends)] if ends else text

    class NoStopChatOpenAI(ChatOpenAI):
        """Reasoning models such as gpt-6-luna reject `stop`, but classic ReAct and
        create_sql_query_chain rely on it. Apply the stop sequences on the client instead."""

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            result = super()._generate(messages, None, run_manager, **kwargs)
            if not stop:
                return result
            generations = []
            for gen in result.generations:
                message = gen.message.model_copy(update={"content": cut(gen.message.text, stop)})
                generations.append(ChatGeneration(message=message, generation_info=gen.generation_info))
            return ChatResult(generations=generations, llm_output=result.llm_output)

    return NoStopChatOpenAI(model=model, timeout=60, max_retries=2)


def custom_resume():
    value = os.getenv("CURRICULO_PDF")
    if not value:
        return None
    path = Path(value).expanduser()
    return (ROOT / path).resolve()
