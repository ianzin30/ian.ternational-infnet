"""Render the academic report from the checked local run artifacts."""

import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.config import ROOT

OUTPUT = ROOT / "output"
FILE = OUTPUT / "pdf" / "ian_trinta_ai-agents_langchain-agents.pdf"
INK = colors.HexColor("#1e2b25")
MUTED = colors.HexColor("#46594d")
RULE = colors.HexColor("#bdc9bf")
PAPER = colors.HexColor("#eff4ef")


def text_style(name, size, leading, *, font="Helvetica", color=INK, after=7):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading, textColor=color,
                          spaceAfter=after, alignment=TA_LEFT)


STYLES = {
    "tag": text_style("tag", 9, 12, font="Helvetica-Bold", color=MUTED, after=13),
    "title": text_style("title", 36, 39, font="Times-Bold", after=15),
    "h1": text_style("h1", 26, 30, font="Times-Bold", after=10),
    "h2": text_style("h2", 13, 17, font="Helvetica-Bold", after=5),
    "body": text_style("body", 10.5, 15),
    "small": text_style("small", 9, 12, color=MUTED),
    "cell": text_style("cell", 9.5, 13, after=0),
    "mono": text_style("mono", 8.6, 12, font="Courier", after=0),
}


def render():
    report = json.loads((OUTPUT / "avaliacao-local.json").read_text())
    live = json.loads((OUTPUT / "chamadas-http.json").read_text())["observacao"][0]
    rows = {r["id"]: r["output"] for r in report["results"]}
    geo = next(c for c in rows["contradicao"]["verification"] if c["job_id"] == "demo-atlas")
    rag = rows["rag-pt-en"]["report"]
    story = []

    def p(value, style="body"):
        story.append(Paragraph(value, STYLES[style]))

    def table(rows, widths):
        cells = [[Paragraph(escape(str(item)), STYLES["cell"]) for item in row] for row in rows]
        grid = Table(cells, colWidths=[n * mm for n in widths], hAlign="LEFT", repeatRows=1)
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PAPER),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, RULE),
            ("LINEBELOW", (0, 1), (-1, -1), 0.45, RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([grid, Spacer(1, 13)])

    def panel(label, lines):
        body = "<br/>".join(escape(line) for line in lines)
        grid = Table([[Paragraph(escape(label), STYLES["h2"])], [Paragraph(body, STYLES["mono"])]],
                     colWidths=[169 * mm], hAlign="LEFT")
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PAPER),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
        ]))
        story.extend([grid, Spacer(1, 13)])

    p("INFNET  /  AGENTES COGNITIVOS COM LANGCHAIN", "tag")
    p("Radar Remoto", "title")
    p("Relatório técnico  /  Ian Trinta", "small")
    p("Para um candidato no Brasil, uma vaga com a etiqueta <i>remote</i> ainda pode exigir residência nos Estados Unidos. O Radar Remoto busca vagas internacionais, aplica restrições antes de ordenar os resultados e apresenta a fonte que sustenta cada decisão.")
    p("O que o candidato consegue conferir", "h2")
    p("Para cada resultado, o agente mostra se a vaga foi recomendada, descartada ou ficou pendente. Ele apresenta o anúncio, o trecho decisivo e as ferramentas chamadas. Quando a moeda e o período são explícitos, pode converter o salário para BRL com a taxa e a data da cotação.")
    panel("Percurso de uma pergunta", [
        "1. O chat identifica a intenção e recupera o contexto da sessão.",
        "2. O executor chama busca, câmbio, SQL ou recuperação documental.",
        "3. O agente aplica restrições e ordena as vagas elegíveis.",
        "4. O verificador cruza afirmações com trechos das fontes.",
        "5. O chat retorna a resposta e guarda a ordem da lista.",
    ])
    p("A aplicação tem dois modos", "h2")
    p("O modo demo usa currículo, anúncios e cotações fictícias. O modelo roteirizado permite reproduzir o fluxo sem chave. Docling, FAISS, SQLite e o classificador NLI são reais nesse modo. O modo real troca os adaptadores de dados e o modelo, mantendo o contrato de chat e as regras de evidência.")
    p("Reprodução: README.md, notebooks 00 a 06 e matriz em docs/progresso.md.", "small")

    story.append(PageBreak())
    p("01  /  DECISÕES DE IMPLEMENTAÇÃO", "tag")
    p("Da chain ao agente", "h1")
    table([
        ("Fase", "Escolha e justificativa"),
        ("1 · Chain", "LCEL separa prompt, modelo, parser e validação Pydantic. A extração mantém campos desconhecidos e pode ser reutilizada pelo agente."),
        ("2 · ReAct", "initialize_agent fica na demonstração didática. O integrador usa function calling estruturado para separar argumentos, ação e observação."),
        ("3 · Memória", "Uma janela e um resumo limitam o histórico. O índice vetorial por sessão recupera perfil, preferências e descartes. IDs preservam a posição exibida."),
        ("4 · Ferramentas", "SQLite responde perguntas sobre candidaturas. A execução de leitura usa uma tabela temporária restrita à sessão. O FAISS carrega um índice preparado pelo Docling."),
        ("5 · Integrador", "AgentExecutor e RunnableWithMessageHistory atendem FastAPI e CLI. A verificação roda antes de persistir a resposta no histórico."),
    ], [35, 134])
    p("Quatro turnos na mesma sessão", "h2")
    panel("Saída observada no teste local", [
        "Busca: Aurora e Orbit foram recomendadas.",
        "Filtro Brasil: a lista numerada só contém vagas elegíveis.",
        "Segunda vaga: Orbit, EUR 5.400/mês → BRL 32.400/mês.",
        "Currículo: Aurora, com Python, FastAPI e PostgreSQL em comum.",
    ])
    p("A posição é resolvida pelos IDs da última lista, sem repetir a busca. Outra sessão não tem acesso à lista nem aos registros de candidatura dessa conversa.", "small")

    story.append(PageBreak())
    p("02  /  EVIDÊNCIA E AVALIAÇÃO", "tag")
    p("O que foi observado", "h1")
    panel("Contradição corrigida dentro do agente", [
        f"Proposta: {geo['claim']}",
        f"Trecho: {geo['evidence']}",
        f"Verificação: {geo['status']}.",
        "Decisão entregue: excluir a vaga da lista numerada.",
    ])
    table([
        ("Métrica local", "Resultado"),
        ("Correção por critérios esperados", f"{report['quality_pass']}/{report['cases']} casos."),
        ("Trajetória de ferramentas", f"{report['trajectory_pass']}/{report['cases']} casos."),
        ("Verificação de afirmações", f"{report['verification'].get('confirmada', 0)}/{report['verification_total']} confirmadas; "
         f"{report['verification'].get('contradita', 0)} contraditas e {report['verification'].get('incerta', 0)} incertas."),
    ], [62, 107])
    p("A proporção de afirmações confirmadas não mede acurácia. O conjunto inclui anúncios ambíguos e uma afirmação preliminar deliberadamente incompatível com o anúncio. Nesses casos, esperar confirmação seria um erro.")
    p("Recuperação antes e depois", "h2")
    before = ", ".join(r["id"] for r in rag["antes"])
    after = ", ".join(r["id"] for r in rag["depois"])
    p(f"Com k=2, a consulta em português recuperou {escape(before)}. A reescrita em inglês retornou {escape(after)} e recuperou Aurora, o alvo esperado. O índice e k permaneceram iguais.")
    p("HTTP real com seleção de ferramenta roteirizada", "h2")
    p("Os registros mostram respostas de " + ", ".join(
        f"{escape(t['source'])} ({escape(t['status'])})" for t in live["fontes"]) +
        ". USD e EUR retornaram cotação pela AwesomeAPI. Os detalhes estão em output/chamadas-http.json.", "small")

    story.append(PageBreak())
    p("03  /  LIMITES E REPRODUÇÃO", "tag")
    p("O que falta comprovar", "h1")
    p("OpenAI e LangSmith", "h2")
    p("As credenciais desses serviços não estavam disponíveis nesta execução. A chamada gerada pela OpenAI, o julgamento semântico e o experimento remoto permanecem pendentes. A regressão em JSON é evidência local; ela não substitui o relatório no LangSmith.")
    p("Interface e defesa", "h2")
    p("A interface provisória é HTML servido pelo FastAPI e foi testada no navegador. O critério 5.5 cita Streamlit nominalmente. O projeto também oferece a CLI, prevista no enunciado para a defesa. A gravação com webcam exige a participação do autor.")
    p("Limites do protótipo", "h2")
    p("O perfil é único por instância e a memória da conversa não sobrevive ao reinício. As fontes podem omitir região, idioma, fuso ou salário. A checagem de localização combina padrões explícitos com inferência; um caso incerto deve continuar incerto. O teste PT/EN usa um corpus pequeno e não estima a taxa de recuperação de anúncios reais.")
    p("Fontes e uso de IA", "h2")
    for label, link in [
        ("Enunciado e rubrica do Infnet", "https://lms.infnet.edu.br/moodle/mod/assign/view.php?id=475711"),
        ("Executor LangChain", "https://reference.langchain.com/python/langchain-classic/agents/openai_tools/base/create_openai_tools_agent"),
        ("Avaliação LangSmith", "https://docs.langchain.com/langsmith/evaluation-types"),
        ("Modelo de inferência NLI", "https://huggingface.co/cross-encoder/nli-deberta-v3-small"),
        ("Remotive", "https://github.com/remotive-com/remote-jobs-api"),
        ("Arbeitnow", "https://www.arbeitnow.com/blog/job-board-api"),
        ("AwesomeAPI", "https://docs.awesomeapi.com.br/api-de-moedas"),
    ]:
        p(f'<link href="{link}" color="#315a45"><u>{label}</u></link>', "small")
    p("OpenAI Codex auxiliou na implementação, nos testes e na redação. Claude Design gerou a interface provisória. Os resultados locais e as chamadas HTTP reportadas foram executados durante o desenvolvimento.", "small")

    def footer(canvas, doc):
        width, _ = A4
        canvas.setStrokeColor(RULE)
        canvas.line(21 * mm, 17 * mm, width - 21 * mm, 17 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(21 * mm, 11 * mm, "RADAR REMOTO   /   RELATÓRIO TÉCNICO")
        canvas.drawRightString(width - 21 * mm, 11 * mm, f"{doc.page:02}")

    FILE.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(FILE), pagesize=A4, title="Radar Remoto - Relatório técnico",
                                 author="Ian Trinta", leftMargin=20 * mm, rightMargin=20 * mm,
                                 topMargin=22 * mm, bottomMargin=23 * mm)
    document.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    render()
