import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.config import DATA, custom_resume, dummy_mode
from src.rag import build_index, index_for_resume
from src.repository import fixtures
from src.verificador import nli_model

def resume_pdf():
    pdf = canvas.Canvas(str(DATA / "curriculo.pdf"), pagesize=A4)
    pdf.setTitle("Currículo fictício para o Radar Remoto")
    for i, line in enumerate((DATA / "curriculo.txt").read_text().splitlines()):
        pdf.drawString(55, 780 - i * 24, line)
    pdf.save()

if __name__ == "__main__":
    resume_pdf()
    print("Chunks no índice:", build_index(fixtures(DATA)))
    custom = custom_resume()
    if custom:
        print("Trechos no índice do currículo configurado:", build_index(fixtures(DATA), custom, index_for_resume(custom)))
    if not dummy_mode() and os.getenv("OPENAI_API_KEY"):
        print("Chunks no índice OpenAI:", build_index(fixtures(DATA), real=True))
        if custom:
            print("Trechos no índice OpenAI do currículo configurado:",
                  build_index(fixtures(DATA), custom, index_for_resume(custom, True), real=True))
    nli_model()
    print("NLI disponível")
