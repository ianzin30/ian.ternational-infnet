"""Build a ZIP containing only the files needed to reproduce the project."""

from zipfile import ZIP_DEFLATED, ZipFile

from src.config import ROOT

SOURCES = (
    ".env.example", ".gitignore", "README.md", "requirements.in", "requirements.txt",
    "data/curriculo.pdf", "data/curriculo.txt", "data/vagas_dummy.json", "data/evaluation.json", "data/evaluation_real.json",
    "web/index.html", "output/avaliacao-local.json", "output/chamadas-http.json",
    "output/langsmith.json", "output/langsmith-real.json",
    "output/pdf/ian_trinta_ai-agents_langchain-agents.pdf",
)
PRIVATE = {"checklist-entrega.md"}
PATTERNS = ("src/*.py", "scripts/*.py", "tests/*.py", "docs/*.md", "docs/diagramas/*.excalidraw",
            "docs/report-assets/*", "notebooks/*.ipynb",
            # The interface: the compiled build FastAPI serves, plus the source needed to rebuild it.
            "web/dist/**/*", "web/src/**/*", "web/public/*", "web/package.json", "web/package-lock.json",
            "web/vite.config.js", "web/HANDOFF.md")

if __name__ == "__main__":
    files = [ROOT / name for name in SOURCES]
    for pattern in PATTERNS:
        files.extend(sorted(ROOT.glob(pattern)))
    # Personal to-do list, not part of the submission.
    files = [path for path in dict.fromkeys(files) if path.is_file() and path.name not in PRIVATE]
    target = ROOT / "output" / "radar-remoto-codigo.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, f"radar-remoto/{path.relative_to(ROOT).as_posix()}")
    print(target)
