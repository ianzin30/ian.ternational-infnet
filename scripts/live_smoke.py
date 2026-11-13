"""Probe actual providers; optionally verify a real model-generated tool call."""

import argparse
import json
import os

from src.config import live_model
from src.demo import provider_function_call

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openai", action="store_true", help="Use the configured OpenAI model instead of replay.")
    args = parser.parse_args()
    if args.openai:
        model = live_model()
        print("Modelo solicitado:", model.model_name)
        os.environ["NOTEBOOK_OPENAI"] = "1"
    result = provider_function_call(live=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["observacao"] or not any(r.get("USD", {}).get("taxa") and
        any(f["status"] == "ok" for f in r.get("fontes", [])) for r in result["observacao"]):
        raise SystemExit("A ferramenta não retornou busca e cotação reais.")
