"""Memória de longo prazo por usuário: SQLite para os fatos, FAISS para a busca por similaridade."""
import logging
import re
import sqlite3
from datetime import datetime, timezone
from threading import RLock

from langchain_community.vectorstores import FAISS

from .rag import embeddings
from .rules import plain

logger = logging.getLogger(__name__)
TIPOS = ("semântica", "episódica", "procedural")
SCHEMA = """CREATE TABLE IF NOT EXISTS memorias (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, tipo TEXT NOT NULL,
 texto TEXT NOT NULL, origem TEXT NOT NULL, criado_em TEXT NOT NULL, UNIQUE(user_id, texto));"""


def similaridade(distance):
    """FAISS devolve L2 ao quadrado; com vetores normalizados, cos = 1 - d/2."""
    return round(max(0.0, min(1.0, 1 - float(distance) / 2)), 2)


class MemoriaLonga:
    def __init__(self, path, real=False):
        self.path, self.real = path, real
        self.lock = RLock()
        self.indices = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def listar(self, user_id):
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT id,tipo,texto,origem,criado_em FROM memorias WHERE user_id=? ORDER BY id DESC", (user_id,))]

    def guardar(self, user_id, tipo, texto, origem):
        texto = " ".join(str(texto).split())[:240]
        if not texto or tipo not in TIPOS:
            return None
        with self.lock, self.connect() as db:
            if len(self.listar(user_id)) >= 200:
                return None
            cursor = db.execute("INSERT OR IGNORE INTO memorias(user_id,tipo,texto,origem,criado_em) VALUES(?,?,?,?,?)",
                                (user_id, tipo, texto, origem, datetime.now(timezone.utc).isoformat(timespec="seconds")))
            if not cursor.rowcount:
                return None
            self.indices.pop(user_id, None)
            return {"id": cursor.lastrowid, "tipo": tipo, "texto": texto, "origem": origem}

    def esquecer(self, user_id, memoria_id):
        with self.lock, self.connect() as db:
            removed = db.execute("DELETE FROM memorias WHERE user_id=? AND id=?", (user_id, memoria_id)).rowcount
            self.indices.pop(user_id, None)
            return bool(removed)

    def buscar(self, user_id, query, k=3):
        """As k memórias mais parecidas com o pedido, com a similaridade medida no FAISS."""
        rows = self.listar(user_id)
        if not rows:
            return []
        try:
            with self.lock:
                index = self.indices.get(user_id)
                if index is None:
                    index = FAISS.from_texts([r["texto"] for r in rows], embeddings(self.real),
                                             metadatas=[{"id": r["id"], "tipo": r["tipo"]} for r in rows])
                    self.indices[user_id] = index
            return [{"id": d.metadata["id"], "tipo": d.metadata["tipo"], "texto": d.page_content,
                     "sim": similaridade(score)} for d, score in index.similarity_search_with_score(query, k=k)]
        except Exception:
            logger.warning("Busca vetorial de memória indisponível; usando as mais recentes.")
            return [{"id": r["id"], "tipo": r["tipo"], "texto": r["texto"], "sim": None} for r in rows[:k]]


def extrair_por_regras(texto):
    """Extração local usada só no modo demo, sem LLM. No modo real o modelo decide pela ferramenta."""
    q, longo, sessao = plain(texto), [], []
    def cap(value):
        value = value.strip()
        return value.upper() if len(value) <= 3 else value[0].upper() + value[1:]
    avoid = re.search(r"(?:nao tenho interesse em|nao quero|evito|evite|nada de)\s+(?:vagas?\s+)?"
                      r"(?:de|com|em|que pedem|que usam)?\s*([a-z0-9#+.]+)", q)
    ignore = {"vaga", "vagas", "empresa", "empresas", "mais", "muito", "nada", "isso", "que", "ver", "saber",
              "o", "a", "os", "as", "um", "uma"}
    if avoid and avoid[1] not in ignore:
        original = re.search(rf"(?i)(?<![\w]){re.escape(avoid[1])}(?![\w])", texto)  # keep the user's casing
        longo.append(("semântica", f"Evita vagas com {cap(original[0] if original else avoid[1])}"))
    if re.search(r"salario|salarios|valor|valores", q) and re.search(r"em reais|em r\$|em brl|reais", q):
        longo.append(("procedural", "Mostrar salário sempre em R$"))
    zone = re.search(r"fuso[^0-9]{0,30}(\d{1,2})\s*h", q) or re.search(r"(\d{1,2})\s*h(?:oras?)?\s+de\s+(?:diferenca|fuso)", q)
    if zone:
        longo.append(("semântica", f"Aceita até {zone[1]} h de diferença de fuso"))
    level = re.search(r"\bsou\s+(junior|pleno|senior)\b", q)
    if level:
        longo.append(("semântica", "Nível " + {"junior": "júnior", "pleno": "pleno", "senior": "sênior"}[level[1]]))
    remember = re.search(r"lembr[ae](?:-se)?\s+(?:de\s+)?que\s+([^.!?\n]+)", texto, re.I)
    if remember:
        longo.append(("semântica", cap(remember[1])))
    if re.search(r"mais curt|resumid|respostas curtas|seja breve|mais breve|mais direto", q):
        sessao.append("Respostas curtas, direto ao ponto")
    if "mais detalh" in q:
        sessao.append("Respostas mais detalhadas")
    if re.search(r"(?:responda|responde|fale|escreva)\s+em\s+ingles", q):
        sessao.append("Responder em inglês")
    return longo, sessao


def skills_evitadas(memorias):
    """Lê as preferências de exclusão que as memórias recuperadas carregam."""
    found = []
    for item in memorias:
        hit = re.search(r"(?i)\bevita(?:r)?\s+(?:vagas?\s+)?(?:com|de|que (?:pedem|usam))\s+(.+?)[.]?$", item["texto"])
        if hit:
            found.extend(part.strip() for part in re.split(r",|\be\b", hit[1]) if part.strip())
    return found
