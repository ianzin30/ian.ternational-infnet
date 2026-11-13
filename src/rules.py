import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from .models import Entidades, Pedido
from .prompts import skills_in


def plain(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))


def sentences(text):
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|[\n;]+", text) if part.strip()]


def snippet(text, pattern):
    return next((s[:450] for s in sentences(text) if re.search(pattern, plain(s))), "")


def geo(job):
    text = "\n".join(filter(None, [job.location, job.description]))
    exclusion = (r"\b(?:us|u\.s\.|usa|uk|eu|europe|germany|canada|united states|north america|"
                 r"united kingdom|emea)\s*(?:[- ]?only|candidates only)\b|"
                 r"\b(?:must (?:be based|reside|live) in|only (?:in|from))\s+(?:the\s+)?"
                 r"(?:us|usa|uk|europe|germany|canada|united states|united kingdom)\b|"
                 r"\b(?:excluding|except|no|not available in)\s+bra[sz]il\b|"
                 r"\b(?:bra[sz]ilian|bra[sz]il-based)\s+(?:applicants|candidates)\s+(?:are\s+)?(?:not eligible|excluded)\b")
    blocked = snippet(text, exclusion)
    if blocked:
        return "descartado", blocked, "O anúncio exclui candidatos no Brasil."
    allowed = snippet(text, r"\b(?:worldwide|globally|work from anywhere|anywhere in the world|"
                           r"including bra[sz]il|remote (?:in|from) (?:bra[sz]il|latam|latin america)|"
                           r"(?:bra[sz]il|latam)\s+only)\b")
    if not allowed and plain(job.location.strip()) in {"brazil", "brasil", "latam", "latin america", "worldwide"}:
        allowed = job.location
    if allowed:
        return "recomendado", allowed, "O anúncio permite trabalho remoto a partir do Brasil."
    return "pendente", snippet(text, r"\bremote\b") or job.location, "O anúncio não confirma elegibilidade no Brasil."


@dataclass(frozen=True)
class Salario:
    low: Decimal
    high: Decimal | None
    currency: str
    period: str
    evidence: str


def salario(job):
    for line in sentences("\n".join(filter(None, [job.salary_hint, job.description]))):
        if re.search(r"(?i)\b(?:not disclosed|unpaid|a combinar)\b", line):
            continue
        period = "month" if re.search(r"(?i)\b(month(?:ly)?|mês|mensal)\b|/mo\b", line) else (
            "year" if re.search(r"(?i)\b(year(?:ly)?|annual(?:ly)?|annum|ano|anual)\b|/yr\b", line) else None)
        if not period:
            continue
        hit = re.search(r"(?i)\b(USD|EUR|BRL)\s*([0-9][0-9,.]*)(\s*k)?(?:\s*[-–]\s*(?:USD|EUR|BRL)?\s*([0-9][0-9,.]*)(\s*k)?)?", line)
        if not hit:
            continue
        def money(value, k):
            value = value.rstrip(".,")
            if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", value):
                value = value.replace(",", "")
            elif "," in value and "." not in value:
                value = value.replace(",", ".")
            return Decimal(value) * (1000 if k else 1)
        try:
            return Salario(money(hit[2], hit[3]), money(hit[4], hit[5]) if hit[4] else None,
                           hit[1].upper(), period, line)
        except ArithmeticError:
            continue
    return None


def interpretar(text):
    t = plain(text)
    explicit_search = bool(re.search(r"\b(?:busque|encontre|procure|mostre|liste)\b.*\bvagas?\b", t))
    intent = ("busca" if explicit_search else
              "cambio" if re.search(r"convert|cambio|em (?:reais|brl)", t) else
              "carta" if "carta" in t else
              "candidaturas" if re.search(r"candidatur|apliquei", t) else
              "curriculo" if re.search(r"curriculo|combina|aderencia", t) else
              "busca" if re.search(r"vaga|remot|brasil|python|aceitam|fuso|utc|ingles", t) else "ajuda")
    pos = next((i for i, word in enumerate(("primeir", "segund", "terceir", "quart", "quint"), 1)
                if re.search(rf"\b{word}[oa]\b", t)), None)
    if not pos and (p := re.search(r"\b(?:vaga|posicao)\s+#?([1-9][0-9]?)\b", t)):
        pos = int(p[1])
    skill = next(iter(skills_in(text)), None)
    pay = re.search(r"(\d+(?:[.,]\d+)?)\s*(k)?\s*(usd|eur|brl)\b", t)
    zone = re.search(r"\butc\s*([+-]\s*\d{1,2})", t)
    lang = re.search(r"\b([abc][12])\b", t)
    period = "year" if re.search(r"\b(anual|ano|year)\b", t) else "month" if pay else None
    return Pedido(intencao=intent, entidades=Entidades(
        cargo="backend" if "backend" in t else None, stack=skill,
        salario_min=float(pay[1].replace(",", ".")) * (1000 if pay[2] else 1) if pay else None,
        moeda=pay[3].upper() if pay else None, periodo=period,
        fuso=int(zone[1].replace(" ", "")) if zone else None, ingles=lang[1].upper() if lang else None,
        aceita_brasil=True if re.search(r"aceita\w* (?:o )?brasil|no brasil|brasil apenas", t) else None,
        posicao=pos,
    ))


def restrictions(job, entities, profile):
    status, evidence, reason = geo(job)
    if status == "descartado":
        return status, evidence, reason
    for skill in entities.evitar_skills:
        quote = snippet(f"{job.title}. {job.description}", rf"(?<![a-z0-9]){re.escape(plain(skill))}(?![a-z0-9])")
        if quote:
            return "descartado", quote, f"Você pediu para evitar {skill} (memória de longo prazo)."
    checks = []
    if entities.fuso is not None:
        zone = re.search(r"\bUTC\s*([+-]\d{1,2})\b", job.description, re.I)
        checks.append(("fuso", int(zone[1]) == entities.fuso if zone else None,
                       snippet(job.description, r"utc\s*[+-]\d") if zone else ""))
    level = entities.ingles or profile.ingles
    if level:
        required = re.search(r"\b([ABC][12])\b", job.description, re.I)
        if required or entities.ingles:
            checks.append(("inglês", required[1].upper() <= level.upper() if required else None,
                           snippet(job.description, r"\b[abc][12]\b") if required else ""))
    if entities.salario_min is not None:
        pay = salario(job)
        value = pay.low if pay and pay.currency == entities.moeda and pay.period == entities.periodo else None
        checks.append(("salário", value >= Decimal(str(entities.salario_min)) if value is not None else None,
                       pay.evidence if pay else ""))
    for label, passed, quote in checks:
        if passed is False:
            return "descartado", quote, f"A vaga não atende ao requisito de {label}."
    for label, passed, quote in checks:
        if passed is None:
            return "pendente", quote or evidence, f"O anúncio não confirma o requisito de {label}."
    if checks:
        # Show every requirement that was checked, not only the Brazil eligibility.
        quotes = [evidence] + [quote for _, _, quote in checks if quote and quote not in evidence]
        evidence = " … ".join(quotes)
        labels = [label for label, _, _ in checks]
        reason += " Também atende aos requisitos de " + " e ".join(
            [", ".join(labels[:-1]), labels[-1]] if len(labels) > 1 else labels) + "."
    return status, evidence, reason
