import sqlite3

from fastapi.testclient import TestClient
import pytest

from scripts.evaluate import cases, check_quality, run_case, tool_trajectory
from src.agente import Radar
from src.api import app
from src.config import DATA
from src.repository import Repository, fixtures
from src.rules import geo, salario


@pytest.mark.parametrize("case", cases(), ids=lambda c: c["id"])
def test_reference_scenarios(case):
    output = run_case({"case": case})
    assert check_quality(output, case), output
    assert tool_trajectory(output, case)["score"], output["tools"]


def test_read_only_sql_hides_other_sessions(tmp_path):
    repository = Repository(tmp_path / "vagas.db")
    repository.save(fixtures(DATA))
    repository.candidatura("a", "demo-aurora", "enviada")
    repository.candidatura("b", "demo-orbit", "salva")
    assert repository.query("SELECT vaga_id FROM candidaturas", "a") == [{"vaga_id": "demo-aurora"}]
    assert repository.query("SELECT vaga_id FROM candidaturas", "b") == [{"vaga_id": "demo-orbit"}]
    assert repository.query("SELECT COUNT(*) AS n FROM candidaturas", "a") == [{"n": 1}]
    with pytest.raises(sqlite3.DatabaseError):
        repository.query("SELECT * FROM main.candidaturas", "a")
    with pytest.raises(ValueError):
        repository.query("DELETE FROM vagas", "a")
    with pytest.raises(sqlite3.DatabaseError):
        repository.query("WITH a AS (SELECT 1) DELETE FROM vagas", "a")
    assert repository.query("SELECT COUNT(*) AS n FROM vagas", "a")[0]["n"] == 5


def test_contract_and_missing_index(tmp_path):
    radar = Radar(db_path=tmp_path / "vagas.db", index_path=tmp_path / "missing", use_nli=False)
    from unittest.mock import patch
    with patch("src.api.get_radar", return_value=radar):
        client = TestClient(app)
        assert client.get("/").status_code == 200
        assert client.post("/chat", json={"session_id": "x", "message": " "}).status_code == 422
        reply = client.post("/chat", json={"session_id": "x", "message": "Mostre vagas remotas de Python"})
        assert reply.status_code == 200
        assert set(reply.json()) == {"answer", "recommendations", "tool_calls", "verification", "mode"}
        result = client.post("/chat", json={"session_id": "x", "message": "Qual combina com meu currículo?"})
        assert result.json()["tool_calls"][0]["status"] == "indisponível"


def test_geography_blocks_conflicting_remote_label():
    job = fixtures(DATA)[0].model_copy(update={"location": "Worldwide", "description": "Remote, US only."})
    assert geo(job)[0] == "descartado"
    ambiguous = fixtures(DATA)[0].model_copy(update={"description": "Remote. Salary: USD 8,000."})
    assert geo(ambiguous)[0] == "pendente"
    assert salario(ambiguous) is None


def test_combined_search_and_curriculum_calls_multiple_tool_categories(tmp_path):
    radar = Radar(db_path=tmp_path / "vagas.db", use_nli=False)
    response = radar.chat("combined", "Busque vagas de Python e compare com meu currículo")
    assert [t.name for t in response.tool_calls] == ["buscar_vagas", "buscar_vagas", "recuperar_contexto"]
    assert "Melhor aderência ao currículo: Senior Python Backend Engineer" in response.answer
    assert any("Currículo:" in v.evidence for v in response.verification)


def test_manual_registration_changes_only_current_session(tmp_path):
    from unittest.mock import patch

    radar = Radar(db_path=tmp_path / "vagas.db", use_nli=False)
    with patch("src.api.get_radar", return_value=radar):
        client = TestClient(app)
        registration = {"session_id": "manual", "vaga_id": "demo-aurora", "status": "enviada"}
        assert client.post("/candidaturas", json=registration).status_code == 404
        assert client.post("/chat", json={"session_id": "manual", "message": "Mostre vagas de Python"}).status_code == 200
        assert client.post("/candidaturas", json=registration).json() == registration
        query = "Quais vagas acima de 5k USD eu ainda não apliquei?"
        assert "Senior Python Backend Engineer" not in radar.chat("manual", query).answer
        assert "Senior Python Backend Engineer" in radar.chat("other", query).answer
