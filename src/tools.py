import html
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from time import monotonic

import httpx

from .models import ToolCall, Vaga
from .rules import plain


def clean(text):
    text = re.sub(r"<(?:br|/p|/li)\b[^>]*>", "\n", str(text or ""), flags=re.I)
    return html.unescape(re.sub(r"<[^>]*>", "", text)).strip()


class Providers:
    def __init__(self, dummy, fixtures):
        self.dummy, self.fixtures = dummy, fixtures
        self._cache = None
        self._lock = Lock()

    def _get(self, url, **kwargs):
        response = httpx.get(url, timeout=10, follow_redirects=True,
                             headers={"User-Agent": "RadarRemoto-academic/1.0", **kwargs.pop("headers", {})}, **kwargs)
        response.raise_for_status()
        return response.json()

    def remotive(self):
        if self.dummy:
            return self.fixtures, "dummy"
        with self._lock:
            if self._cache and monotonic() - self._cache[0] < 21600:
                return self._cache[1], "cache"
            try:
                payload = self._get("https://remotive.com/api/remote-jobs")
                jobs = [Vaga(id=f"remotive-{j['id']}", title=j["title"], company=j["company_name"],
                            source="Remotive", url=j["url"], description=clean(j.get("description")),
                            location=clean(j.get("candidate_required_location")),
                            salary_hint=clean(j.get("salary"))) for j in payload["jobs"]]
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                if self._cache:
                    return self._cache[1], "cache desatualizado"
                raise
            self._cache = monotonic(), jobs
            return jobs, "ok"

    def arbeitnow(self):
        if self.dummy:
            return [], "dummy"
        payload = self._get("https://www.arbeitnow.com/api/job-board-api")
        return [Vaga(id=f"arbeitnow-{j['slug']}", title=j["title"], company=j["company_name"],
                     source="Arbeitnow", url=j["url"], description=clean(j.get("description")),
                     location=clean(j.get("location"))) for j in payload["data"] if j.get("remote")], "ok"

    def buscar(self, terms=""):
        def run(name, function):
            start = monotonic()
            try:
                jobs, status = function()
                jobs = [j for j in jobs if not terms or
                        all(word in plain(j.title + " " + j.description) for word in plain(terms).split())]
                detail = f"{len(jobs)} vaga(s) correspondem à busca."
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                jobs, status, detail = [], "erro", f"Fonte indisponível ({type(exc).__name__})."
            return jobs, ToolCall(name="buscar_vagas", source=name, status=status, detail=detail,
                                  duration_ms=round((monotonic() - start) * 1000))
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run, "Remotive", self.remotive)
            second = pool.submit(run, "Arbeitnow", self.arbeitnow)
            a, trace_a = first.result()
            b, trace_b = second.result()
        return list({job.id: job for job in a + b}.values())[:30], [trace_a, trace_b]

    def cotacao(self, currency):
        if currency == "BRL":
            return Decimal("1"), None, "Moeda original"
        if currency not in {"USD", "EUR"}:
            raise ValueError("Moeda não suportada.")
        if self.dummy:
            return Decimal({"USD": "5.00", "EUR": "6.00"}[currency]), "2026-01-01", "Cotação fictícia"
        key = os.getenv("AWESOMEAPI_KEY")
        payload = self._get(f"https://economia.awesomeapi.com.br/json/last/{currency}-BRL",
                            headers={"x-api-key": key} if key else {})
        rate = payload[f"{currency}BRL"]
        date = datetime.fromtimestamp(int(rate["timestamp"]), timezone.utc).date().isoformat()
        return Decimal(rate["bid"]), date, "AwesomeAPI"
