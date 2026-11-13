import json
import sqlite3

from .models import Vaga

SCHEMA = """
CREATE TABLE IF NOT EXISTS vagas (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, company TEXT NOT NULL, source TEXT NOT NULL,
 url TEXT NOT NULL, salary_min REAL, currency TEXT, period TEXT);
CREATE TABLE IF NOT EXISTS candidaturas (
 session_id TEXT NOT NULL, vaga_id TEXT NOT NULL REFERENCES vagas(id),
 status TEXT NOT NULL CHECK(status IN ('salva','enviada','descartada')),
 PRIMARY KEY(session_id, vaga_id));
"""


class Repository:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def save(self, jobs):
        from .rules import salario
        rows = []
        for job in jobs:
            pay = salario(job)
            rows.append((job.id, job.title, job.company, job.source, job.url,
                         float(pay.low) if pay else None, pay.currency if pay else None, pay.period if pay else None))
        with self.connect() as db:
            db.executemany("""INSERT INTO vagas VALUES(?,?,?,?,?,?,?,?)
              ON CONFLICT(id) DO UPDATE SET title=excluded.title, company=excluded.company,
              source=excluded.source,url=excluded.url,salary_min=excluded.salary_min,
              currency=excluded.currency,period=excluded.period""", rows)

    def candidatura(self, session_id, job_id, status):
        with self.connect() as db:
            db.execute("""INSERT INTO candidaturas VALUES (?,?,?)
             ON CONFLICT(session_id,vaga_id) DO UPDATE SET status=excluded.status""", (session_id, job_id, status))

    def query(self, sql, session_id, params=()):
        sql = sql.strip().removesuffix(";")
        if not sql.lower().startswith(("select ", "select\n", "with ", "with\n")):
            raise ValueError("Somente consultas de leitura são permitidas.")
        with sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            # Materialize only this session before permitting generated SQL.
            db.execute("CREATE TEMP TABLE candidaturas AS SELECT vaga_id,status FROM main.candidaturas WHERE session_id=?", (session_id,))
            db.execute("PRAGMA query_only=ON")
            db.set_authorizer(lambda action, table, col, schema, origin:
                sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ and
                (table not in {"vagas", "candidaturas"} or
                 (table == "candidaturas" and schema not in {None, "temp"}))
                else sqlite3.SQLITE_OK)
            budget = 1000
            def progress():
                nonlocal budget
                budget -= 1
                return int(budget <= 0)
            db.set_progress_handler(progress, 1000)
            return [dict(row) for row in db.execute(sql, params).fetchmany(20)]


def fixtures(data):
    return [Vaga.model_validate(item) for item in json.loads((data / "vagas_dummy.json").read_text())]
