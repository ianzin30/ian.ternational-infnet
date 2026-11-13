from uuid import uuid4

from src.agente import Radar
from src.config import dummy_mode


if __name__ == "__main__":
    radar = Radar(dummy=dummy_mode())
    session_id = uuid4().hex
    print(f"Radar Remoto | modo {'demo' if radar.dummy else 'real'} | /sair encerra")
    while True:
        try:
            question = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question == "/sair":
            break
        if not question:
            continue
        response = radar.chat(session_id, question)
        print("Radar:", response.answer)
        for item in response.tool_calls:
            print(f"  ferramenta: {item.name} · {item.source} · {item.status} · {item.duration_ms} ms")
        for item in response.verification:
            print(f"  {item.status}: {item.claim} | {item.evidence or 'sem trecho'}")
        for job in response.recommendations:
            print(f"  {job.status}: {job.title} | {job.reason} | {job.url}")
