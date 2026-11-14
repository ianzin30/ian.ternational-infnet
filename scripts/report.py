"""Build the ian.ternational report offline from versioned evidence and captured UI."""
import ast
import json
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "report-assets"
OUT = ROOT / "output"
PDF = OUT / "pdf" / "ian_trinta_ai-agents_langchain-agents.pdf"
INK, MUTED, ACCENT = map(HexColor, ("#17282B", "#475E63", "#086779"))
PAPER, SOFT, RULE = map(HexColor, ("#FAFAF6", "#EDF4F2", "#C9DAD7"))
MARK = HexColor("#FFDC68")
WIDTH, HEIGHT = A4
M = 46
W = WIDTH - 2*M
REPO = "https://github.com/ianzin30/ian.ternational-infnet/blob/feat/ui-vue/"
ASSIGNMENT = "https://lms.infnet.edu.br/moodle/mod/assign/view.php?id=475711"
LABELS = {
    "demo-moon": "Moon Studio", "demo-atlas": "Atlas Systems", "demo-aurora": "Aurora Labs"
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def notebook_stdout(name, cell):
    nb = read(ROOT / "notebooks" / (name + ".ipynb"))
    return "".join("".join(out["text"]) for out in nb["cells"][cell]["outputs"] if out.get("name") == "stdout")


def link(label, url):
    return f'<link href="{escape(url)}" color="#086779"><u>{escape(label)}</u></link>'


def code(value):
    return f'<font face="Courier">{escape(value)}</font>'


def score(rows, key):
    return f'{sum(row["scores"][key]["score"] == 1 for row in rows)}/{len(rows)}'


class Report:
    def __init__(self, file):
        self.c = Canvas(str(file), pagesize=A4, pageCompression=1, invariant=True)
        self.c.setTitle("ian.ternational | Relatório técnico")
        self.c.setAuthor("Ian Trinta")
        self.c.setSubject("Arquitetura e avaliação do agente de vagas remotas")
        self.n = 0
        self.y = 0

    def para(self, body, *, x=M, top=None, width=W, size=11.5, leading=None,
             font="Helvetica", color=INK, gap=10):
        style = ParagraphStyle("text", fontName=font, fontSize=size,
                               leading=leading or size*1.35, textColor=color)
        p = Paragraph(body, style)
        _, h = p.wrap(width, HEIGHT)
        if top is None:
            top = self.y
            self.y += h + gap
        p.drawOn(self.c, x, HEIGHT-top-h)
        return h

    def line(self, x, y, x2, y2, color=RULE, weight=0.65):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(weight)
        self.c.line(x, HEIGHT-y, x2, HEIGHT-y2)

    def rect(self, x, y, w, h, fill):
        self.c.setFillColor(fill)
        self.c.rect(x, HEIGHT-y-h, w, h, fill=1, stroke=0)

    def start(self, eyebrow, title, deck=None, cover=False):
        self.n += 1
        self.rect(0, 0, WIDTH, HEIGHT, PAPER)
        self.line(M, 34, WIDTH-M, 34, ACCENT, 1.6)
        self.c.bookmarkPage(f"p{self.n}")
        self.c.addOutlineEntry(title.replace("<br/>", " "), f"p{self.n}")
        self.y = 48
        self.para(eyebrow, font="Helvetica-Bold", size=8.8, color=ACCENT, gap=15)
        if cover:
            with Image.open(ASSETS / "ianternational-wordmark.png") as wordmark:
                h = 42
                self.c.drawImage(ImageReader(wordmark), M, HEIGHT-self.y-h,
                                 h*wordmark.width/wordmark.height, h)
            self.y += 59
        self.para(title, size=43 if cover else 37, leading=45 if cover else 40,
                  font="Times-Bold", gap=14)
        if deck:
            self.para(deck, size=12.4, leading=17, color=MUTED, gap=22)

    def end(self):
        if self.y > 785:
            raise ValueError(f"Página {self.n} excedeu a área de conteúdo: {self.y:.1f} pt")
        self.line(M, 795, WIDTH-M, 795)
        self.para("ian.ternational  /  Ian Trinta", top=805, size=8, color=MUTED, font="Helvetica-Bold")
        self.c.setFillColor(ACCENT)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawRightString(WIDTH-M, HEIGHT-815, f"{self.n:02} / 10")
        self.c.showPage()

    def heading(self, title):
        self.para(title, size=15.5, font="Helvetica-Bold", gap=7)

    def caption(self, number, body):
        self.para(f"<b>{number}</b>  {body}", size=9.6, leading=13, color=MUTED, gap=15)

    def band(self, label, body):
        y = self.y
        h = self.para(body, x=M+16, top=y+30, width=W-30, size=11, leading=15)
        # Paint only the rule; body and labels stay on the document paper.
        self.line(M, y, WIDTH-M, y, ACCENT, 1)
        self.para(label, x=M+16, top=y+10, size=9, font="Helvetica-Bold", color=ACCENT)
        self.y = y+30+h+19

    def grid(self, rows, shares, size=10.6, padding=8):
        cells = []
        for i, row in enumerate(rows):
            style = ParagraphStyle("cell", fontName="Helvetica-Bold" if i == 0 else "Helvetica",
                                   fontSize=size, leading=size*1.32, textColor=INK)
            cells.append([Paragraph(v, style) for v in row])
        tbl = Table(cells, colWidths=[W*s for s in shares], hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SOFT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.65, RULE),
            ("TOPPADDING", (0, 0), (-1, -1), padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        _, h = tbl.wrap(W, HEIGHT)
        tbl.drawOn(self.c, M, HEIGHT-self.y-h)
        self.y += h+15

    def diagram(self, steps):
        y = self.y
        gap = 16
        w = (W-gap*(len(steps)-1))/len(steps)
        h = 79
        for i, (title, body) in enumerate(steps):
            x = M+i*(w+gap)
            self.rect(x, y, w, h, SOFT)
            self.line(x, y, x+w, y, ACCENT, 1)
            self.para(title, x=x+8, top=y+11, width=w-16, size=10.3, font="Helvetica-Bold")
            self.para(body, x=x+8, top=y+32, width=w-16, size=9.6, leading=12, color=MUTED)
            if i < len(steps)-1:
                a = x+w+2
                self.line(a, y+39, a+12, y+39, ACCENT, 1)
                self.line(a+9, y+36, a+12, y+39, ACCENT, 1)
                self.line(a+9, y+42, a+12, y+39, ACCENT, 1)
        self.y += h+17

    def shot(self, name, crop, *, marks=(), width=W, x=M):
        """Place a clipped screenshot and draw callouts as PDF vectors."""
        file = ASSETS / name
        with Image.open(file) as im:
            iw, ih = im.size
            l, t, r, b = crop
            assert 0 <= l < r <= iw and 0 <= t < b <= ih
            clipped = BytesIO()
            im.crop(crop).save(clipped, format="PNG")
            clipped.seek(0)
        k = width/(r-l)
        h = (b-t)*k
        top = self.y
        c = self.c
        c.saveState()
        c.drawImage(ImageReader(clipped), x, HEIGHT-top-h, width, h)
        for label, (ml, mt, mr, mb) in marks:
            xx, yy = x+(ml-l)*k, top+(mt-t)*k
            ww, hh = (mr-ml)*k, (mb-mt)*k
            c.setStrokeColor(MARK)
            c.setLineWidth(1.5)
            c.roundRect(xx, HEIGHT-yy-hh, ww, hh, 5, fill=0, stroke=1)
            c.setFillColor(MARK)
            c.circle(xx+ww+8, HEIGHT-yy-hh/2, 6.5, stroke=0, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(xx+ww+8, HEIGHT-yy-hh/2-2.7, str(label))
        c.restoreState()
        self.line(x, top+h, x+width, top+h)
        self.y += h+7

    def logos(self):
        y = self.y
        self.line(M, y, M+W, y)
        labels = [("python", "Python"), ("langchain", "LangChain"), ("openai", "OpenAI"),
                  ("fastapi", "FastAPI"), ("vue", "Vue"), ("langsmith", "LangSmith")]
        for i, (icon, label) in enumerate(labels):
            x = M+(i+.5)*W/len(labels)
            self.c.drawImage(str(ASSETS/(icon+".png")), x-24, HEIGHT-y-39, 48, 24, mask="auto")
            self.c.setFont("Helvetica-Bold", 8.5)
            self.c.setFillColor(INK)
            self.c.drawCentredString(x, HEIGHT-y-53, label)
        self.y += 63


def render():
    demo = read(OUT / "langsmith.json")
    real = read(OUT / "langsmith-real.json")
    chat_model = code(real["modelo"])
    compare_url = real["dataset_url"] + "/compare?selectedSessions=" + real["url"].rsplit("/", 1)[-1]
    local = {r["id"]: r["output"] for r in read(OUT / "avaliacao-local.json")["results"]}
    real_cases = {r["case"]: r["output"]["turns"] for r in real["casos"]}
    evidence_http = read(OUT / "chamadas-http.json")["observacao"][0]
    function_call = ast.literal_eval(notebook_stdout("03_agente_react", 5))
    rag = local["rag-pt-en"]["report"]
    cv = read(ASSETS / "perfil-curriculo.json")
    notebook_profile = ast.literal_eval(notebook_stdout("02_chain_mvp", 3).split("invoke:\n", 1)[1].split("\nbatch:", 1)[0])
    react = ast.literal_eval(notebook_stdout("03_agente_react", 3))
    action = next(c for c in react["callbacks"] if c["evento"] == "action")
    obs = next(c for c in react["callbacks"] if c["evento"] == "observation")
    combined = real_cases["busca-com-curriculo"][0]
    atlas_demo = next(v for v in local["contradicao"]["verification"] if v["job_id"] == "demo-atlas")
    atlas_real = next(v for v in real_cases["elegibilidade-brasil"][0]["verification"] if v["job_id"] == "demo-atlas")
    atlas_card = next(v for v in real_cases["elegibilidade-brasil"][0]["recommendations"] if v["id"] == "demo-atlas")
    rows = real["casos"]
    marks = {key: score(rows, key) for key in ("correcao_semantica", "rotas", "trajetoria_modelo")}
    demo_quality = demo["metricas"]["correcao_semantica"]
    demo_path = demo["metricas"]["trajetoria"]
    PDF.parent.mkdir(parents=True, exist_ok=True)
    r = Report(PDF)
    p = r.para

    r.start("INFNET  /  AGENTES COGNITIVOS COM LANGCHAIN  /  2026", "Seu agente para<br/>vagas remotas",
            "Um assistente para quem mora no Brasil e quer buscar vagas internacionais, entender as restrições de cada anúncio e decidir quais oportunidades valem a candidatura.", cover=True)
    p("RELATÓRIO TÉCNICO  /  IAN TRINTA", size=9.5, color=ACCENT, font="Helvetica-Bold", gap=32)
    r.heading("O que você pode pedir")
    r.grid([("Pedido", "Como o agente ajuda"),
            ("“Encontre vagas remotas que aceitam Brasil.”",
             "Busca anúncios, separa as vagas por elegibilidade e mostra o trecho que sustenta cada decisão."),
            ("“Qual delas combina com meu currículo?”",
             "Recupera trechos do currículo e aponta habilidades em comum com o anúncio."),
            ("“Converta o salário da segunda para reais.”",
             "Usa a lista da conversa para identificar a vaga e converte o salário quando o anúncio informa moeda e período.")], [.45,.55])
    r.y += 18
    r.logos()
    r.end()

    r.start("01  /  PROBLEMA E PRIMEIRA CHAIN", "Uma vaga remota pode<br/>excluir o Brasil",
            "“Remote” não diz de onde você pode trabalhar. Se o anúncio omite a região, a vaga fica pendente. Se restringe a contratação aos EUA, o agente mostra por que ela saiu da lista.")
    r.shot("app-atlas.png", (402, 365, 1200, 578), marks=[
        (1, (439,430,714,492)), (2,(826,430,1164,572))], width=420)
    r.caption("FIG. 01", "Painel do app em modo demo. <b>1</b> O anúncio restringe a vaga aos EUA. <b>2</b> O agente mostra a decisão ao lado da fonte.")
    r.heading("A chain transforma o currículo em dados")
    p("Para comparar o anúncio com o candidato, o sistema precisa de campos conhecidos, como habilidades e idioma. A primeira versão usa uma sequência fixa.", size=10.8)
    r.diagram([("Prompt", "Pede apenas dados explícitos."), ("Extração", "Regras locais ou LLM."),
               ("Parser", "Converte a saída JSON."), ("Validação", "Confere o esquema do perfil.")])
    p("<b>Entrada do exemplo local:</b> "+escape(cv["excerpt"]), size=10)
    r.grid([("Origem", "Campo preenchido", "Campo sem informação"),
            ("Notebook 02. Currículo fictício.", code(f"ingles = {notebook_profile['ingles']!r}"),
             code(f"pretensao_salarial = {notebook_profile['pretensao_salarial']}")),
            ("Currículo de Ian. Recorte executado localmente.", code(", ".join(cv["profile"]["skills"])),
             code("pretensao_salarial = null"))], [.39,.29,.32], size=9.5)
    p("<b>Por que LCEL?</b> O mesmo fluxo aceita regras locais ou um LLM sem mudar o JSON. O recorte do autor usou regras locais. O notebook 02 demonstra também <font face='Courier'>@chain</font>, <i>invoke</i>, <i>batch</i> e <i>stream</i>.", size=10.4, gap=0)
    r.end()

    r.start("02  /  FERRAMENTAS E REACT", "O agente pode pedir<br/>uma ferramenta",
            "Extrair um perfil é um caminho fixo. Buscar uma vaga exige decidir se vale consultar uma fonte e usar o resultado antes de responder.")
    r.grid([("ReAct clássico. Notebook 03", "Executor do chat. Suíte real"),
            (f"<b>Action:</b> {code(action['tool'])}<br/><b>Action Input:</b> {code(action['input'])}<br/><b>Observation:</b> Remotive devolveu anúncios, entre eles Senior React Full-stack Developer.",
             f"<b>Rota:</b> {code(combined['route'])}<br/><b>Chamadas estruturadas registradas:</b><br/>{code(combined['model_tools'][0])}<br/>{code(combined['model_tools'][1])}")], [.5,.5])
    r.caption("SAÍDA 02", f"À esquerda, callbacks de uma execução com {react['modelo']} e consulta HTTP ({obs['duration_ms']} ms na ferramenta); a observação está resumida. À direita, chamadas do modelo real com dados fixos.")
    p("O ciclo é parecido nos dois casos. O clássico transmite ação e argumento em texto e encerra com a resposta do próprio agente. O chat usa chamadas estruturadas dentro de um roteiro que ainda aplica regras e verifica a evidência.")
    r.diagram([("Ação", "O modelo indica a ferramenta."),
               ("Observação", "O app devolve o resultado."),
               ("Próximo passo", "O modelo pede outra ação ou encerra.")])
    r.band("POR QUE LANGCHAIN", "LangGraph daria controle explícito sobre um grafo de estados. CrewAI e AutoGen são opções para coordenar vários agentes. Neste projeto, um só executor cobre o domínio e permite reaproveitar as chains do MVP. O RouterChain escolhe a rota, e os callbacks registram ação, observação e uso do modelo.")
    p("O prompt PTCF define papel, tarefa, contexto e formato. Nos exemplos, “Remote” deixa a vaga pendente; “US only” leva ao descarte. A instrução manda checar região, restrições, aderência e evidência nessa ordem. O callback registra ações e observações.", size=10.8)
    r.end()

    r.start("03  /  MEMÓRIA CONVERSACIONAL", "“A segunda vaga”<br/>tem significado",
            "O app guarda a ordem da lista por sessão. Assim, um pedido de câmbio pode recuperar o segundo ID sem repetir a busca.")
    fx = real_cases["cambio-com-memoria"]
    r.grid([("Turno", "Pedido", "Saída registrada"),
            ("1", escape(fx[0]["message"]), "1. Aurora Labs<br/><b>2. Python Platform Engineer · Orbit Works</b>"),
            ("2", escape(fx[1]["message"]), "<b>R$ 32.400,00 por mês</b><br/>1 EUR = R$ 6,00 na cotação fixa do teste.")], [.12,.40,.48])
    r.shot("langsmith-memory.jpg", (0, 0, 875, 168), marks=[
        (1, (443, 31, 604, 57)), (2, (87, 134, 500, 160))])
    r.caption("FIG. 02", "Saída de <i>cambio-com-memoria</i> na suíte real. <b>1</b> Valor convertido. <b>2</b> A referência aponta para a Orbit, que ocupava a posição 2 na lista anterior.")
    r.heading("Dois tipos de memória, dois usos")
    p("<b>Na conversa.</b> O notebook 04 demonstra <font face='Courier'>ConversationBufferMemory</font>. No agente final, <font face='Courier'>RunnableWithMessageHistory</font> lê e grava as mensagens da sessão. A posição da vaga vem da lista que o app guardou; janela, resumo e busca vetorial ajudam a limitar o contexto.")
    p("<b>Entre conversas.</b> No caso <i>preferencia-entre-sessoes</i>, o modelo chamou <font face='Courier'>guardar_memoria</font> ao receber o pedido para evitar Docker. O app recuperou a preferência em outra sessão do mesmo usuário e deixou a Orbit fora da lista.")
    r.band("ESCOLHA DE PROJETO", "A memória curta acompanha a conversa atual. A longa guarda fatos, episódios e preferências de procedimento por usuário. A separação evita que uma referência como “a segunda” seja reaproveitada fora da sessão.")
    r.end()

    r.start("04  /  FERRAMENTAS E RECUPERAÇÃO", "Cada fonte responde<br/>a uma pergunta",
            "Um anúncio, uma cotação e um histórico de candidaturas exigem métodos diferentes. O agente reúne os resultados no mesmo turno quando o pedido precisa de mais de uma fonte.")
    r.grid([("Pergunta", "Tipo e fonte", "Decisão técnica"),
            ("Quais vagas e quanto pagam?", "APIs externas<br/>Remotive, Arbeitnow e AwesomeAPI",
             "Busca em paralelo; o cálculo do câmbio segue uma regra fixa quando o anúncio informa moeda e período."),
            ("A quais vagas ainda não me candidatei?", "Texto para SQL<br/>SQLite",
             "O modelo gera SQL. O app permite leitura e restringe as candidaturas à sessão."),
            ("Qual vaga combina com o perfil?", "Busca semântica<br/>Docling e FAISS",
             "Docling extrai o texto do PDF. O FAISS consulta o índice existente e devolve os trechos mais próximos.")], [.29,.29,.42])
    r.heading("Uma consulta em português perdeu a vaga certa")
    top = lambda side: " · ".join(LABELS.get(v["id"], v["id"]) for v in rag[side])
    r.grid([("Consulta", "Dois primeiros resultados", "Aurora"),
            (escape(rag["consulta_original"]), escape(top("antes")), "Fora"),
            (escape(rag["reescrita"]), escape(top("depois")), "<b>1º lugar</b>")], [.38,.43,.19])
    r.caption("SAÍDA 04", "Caso <i>rag-pt-en</i>, com "+code("paraphrase-multilingual-MiniLM-L12-v2")+" local. Mesmo índice, mesmo corpus fictício, mesmo k = 2. Mudou apenas a consulta.")
    r.band("POR QUE REESCREVER", "Os anúncios estavam em inglês. A primeira consulta recuperou documentos, mas deixou de fora o alvo conhecido. A reescrita recuperou Aurora sem reconstruir o índice; um único caso não mede a melhora geral da busca.")
    r.end()

    r.start("05  /  AGENTE INTEGRADOR", "O integrador decide,<br/>executa e verifica",
            "A chain inicial seguia passos fixos. O agente final é híbrido: o código organiza o turno e o modelo escolhe ferramentas dentro desse fluxo.")
    r.diagram([("Intenção", "Identifica a rota e as restrições."),
               ("AgentExecutor", "O modelo pede ferramentas."),
               ("Verificação", "Regras e NLI confrontam a evidência."),
               ("Resposta", "Redige e guarda o turno.")])
    p("O app usa "+code("create_openai_tools_agent")+" com "+code("AgentExecutor")+". Se o modelo omitir uma ferramenta exigida pela rota, o código pode chamá-la. A avaliação registra essa chamada à parte.", size=10.8)
    r.heading("Atlas: a mesma decisão, duas evidências")
    r.grid([("Execução", "O que foi verificado", "O que chegou à lista"),
            ("Demo com contradição deliberada", f"{escape(atlas_demo['claim'])}<br/><b>Veredito: {escape(atlas_demo['status'])}.</b>", "Atlas excluída."),
            ("Modelo real com dados fixos", f"{escape(atlas_real['claim'])}<br/>NLI: {escape(atlas_real['nli_label'])}.<br/><b>Veredito: {escape(atlas_real['status'])}.</b>", f"Atlas: {escape(atlas_card['status'])}.")], [.29,.48,.23])
    r.caption("SAÍDA 05", "O anúncio dizia “Remote, US only”. Na demo, a proposta dizia que o Brasil era elegível. No caso real, o agente fez a afirmação negativa: a regra geográfica e a checagem de coerência a sustentaram, enquanto o NLI ficou neutro.")
    r.heading("Qual modelo faz o quê")
    r.grid([("Papel", "Modelo e função"),
            ("Interpretar, agir e redigir", chat_model+" · classifica a intenção, pede ferramentas, gera SQL e redige no modo real."),
            ("Recuperar trechos", code("text-embedding-3-small")+" · transforma texto em vetores no modo real. A demo usa MiniLM multilíngue."),
            ("Verificar afirmações", code("cross-encoder/nli-deberta-v3-small")+" · compara anúncio e afirmação antes da redação. No modo real, "+chat_model+" também checa coerência.")], [.28,.72], size=9.7, padding=5)
    r.end()

    r.start("06  /  AVALIAÇÃO NO LANGSMITH", "O que os testes mediram",
            f"A suíte principal avaliou {escape(real['modelo'])} em seis cenários. Anúncios, cotação e currículo ficaram fixos; a decisão do modelo e sua resposta foram geradas durante a execução.")
    r.shot("langsmith-table.jpg", (0, 0, 632, 362), marks=[
        (1, (306,5,377,61)), (2,(423,5,492,61)), (3,(548,5,604,61))])
    r.caption("FIG. 03", "LangSmith, suíte real. <b>1</b> Correção semântica. <b>2</b> Rotas. <b>3</b> Trajetória do modelo. Cada linha representa um caso.")
    r.grid([("Avaliação", "Qualidade semântica", "Ferramentas", "Rotas"),
            ("Demo com dados fixos", f"{demo_quality['passou']}/{demo_quality['total']}", f"{demo_path['passou']}/{demo_path['total']} · execução", "Não medida"),
            ("Modelo real com dados fixos", marks["correcao_semantica"], marks["trajetoria_modelo"]+" · escolha do modelo", marks["rotas"])],
           [.28,.24,.30,.18], size=10)
    p("<b>Correção semântica:</b> na suíte real, "+chat_model+" atua também como juiz em uma chamada separada. Ele recebe o critério e o registro da execução. A demo também usa um juiz OpenAI, apesar de o agente ser roteirizado.", size=10.5, gap=7)
    p("<b>Rotas e ferramentas:</b> o código compara os registros com o esperado em cada turno. Na suíte real, a ordem entre ferramentas independentes não importa; a trajetória só passa se o app não completar nenhuma chamada obrigatória.", size=10.5, gap=7)
    p(link("Abrir o experimento com modelo real", compare_url), size=10, gap=0)
    r.end()

    r.start("07  /  UM CASO ABERTO", "Por que este caso passou",
            "O pedido foi buscar vagas para o Brasil e compará-las com o currículo fictício. O teste esperava que o modelo pedisse busca e recuperação documental no mesmo turno.")
    r.shot("langsmith-table.jpg", (0, 311, 632, 362))
    r.heading("Esperado")
    r.shot("langsmith-reference.jpg", (0, 107, 460, 298),
           marks=[(1,(77,166,235,228))], width=305)
    r.heading("Obtido")
    r.shot("langsmith-output.jpg", (0, 0, 835, 315),
           marks=[(3,(23,6,808,30)),(2,(24,127,199,152)),(1,(45,243,205,309))])
    r.caption("FIG. 04", "Recortes da mesma execução: nota, referência e saída. <b>1</b> As duas ferramentas esperadas aparecem na saída. <b>2</b> O app não precisou completar chamadas. <b>3</b> Aurora lidera por Python, FastAPI e PostgreSQL em comum.")
    r.end()

    r.start("08  /  ANÁLISE E LIMITES", "O acerto da consulta<br/>não garante a redação",
            "As notas respondem a critérios definidos antes dos testes. Ler a saída completa mostra problemas que uma nota binária pode deixar passar.")
    sql = real_cases["historico-sql"][0]
    r.grid([("O que a consulta fez", "O que o usuário leu"),
            (f"SQLite retornou <b>{escape(sql['sql_rows'][0]['company'])}</b>. A consulta aplicou a faixa em USD e excluiu candidaturas enviadas da sessão.",
             escape(sql["answer"].split("\n\n", 1)[0]))], [.50,.50])
    r.caption("SAÍDA 06", "Caso <i>historico-sql</i>, suíte real. O juiz aprovou o resultado esperado; a ressalva na resposta confunde o usuário.")
    r.grid([("Trecho da consulta", "O que restringe"),
            (code("currency = 'USD' AND salary_min > 5000"), "Moeda e valor mínimo."),
            (code("NOT EXISTS (... status = 'enviada')"), "Vagas sem candidatura enviada na sessão.")], [.57,.43], size=10)
    p("Uma melhoria é levar os filtros executados para o rascunho que o redator recebe e testar explicitamente se a resposta preserva esses filtros.")
    r.heading("A consulta HTTP foi verificada à parte")
    statuses = ", ".join(f"{t['source']} ({t['status']})" for t in evidence_http["fontes"])
    function_tool = next(c["tool"] for c in function_call["callbacks"] if c["evento"] == "action")
    p(f"O notebook 03 registra OpenAI chamando {code(function_tool)} por function calling, com HTTP real. Em outro registro, com escolha roteirizada, {escape(statuses)} responderam, e a {escape(evidence_http['USD']['fonte'])} retornou a cotação USD de {escape(evidence_http['USD']['data'])}. Nos seis casos do LangSmith, os dados externos ficaram fixos.", size=10.8)
    r.band("O QUE OS NÚMEROS NÃO MEDIRAM", "As suítes têm casos e critérios diferentes; não medem ganho de desempenho entre modos. Os seis acertos descrevem uma execução com o mesmo modelo no papel de agente e de juiz. Uma revisão humana ajudaria a verificar as notas. Em uso real, fontes podem omitir dados, a redação pode variar e o histórico curto se perde ao reiniciar. O caso SQL também deveria testar anúncios sem período informado.")
    r.end()

    r.start("09  /  REPRODUÇÃO E REFERÊNCIAS", "Como conferir o projeto",
            "Os notebooks guardam as saídas de cada fase. A seção Evidência de cada notebook associa os itens da rubrica às células correspondentes.")
    r.grid([("Itens da rubrica", "Onde encontrar a evidência"),
            ("1.1 a 1.6 · Chain", link("Notebook 02", REPO+"notebooks/02_chain_mvp.ipynb")+" · arquitetura híbrida, planejamento e perfil em JSON. Compare LCEL e @chain."),
            ("2.1 a 2.6 · ReAct", link("Notebook 03", REPO+"notebooks/03_agente_react.ipynb")+" · escolha do orquestrador, ReAct clássico, RouterChain, HTTP, prompt PTCF e parser com recuperação."),
            ("3.1 a 3.6 · Memória", link("Notebook 04", REPO+"notebooks/04_memoria.ipynb")+" · CoALA, comparação de ferramentas, ConversationBufferMemory, intenção e conversa em vários turnos."),
            ("4.1 a 4.5 · Ferramentas", link("Notebook 05", REPO+"notebooks/05_ferramentas_rag.ipynb")+" · APIs, SQL e recuperação. O "+link("Notebook 01", REPO+"notebooks/01_indexacao.ipynb")+" mostra como o índice foi preparado."),
            ("5.1 a 5.4 e 5.6 · Integração", link("Notebook 06", REPO+"notebooks/06_integrador_avaliacao.ipynb")+" · verificação, executor e histórico. Resultados: "+link("suíte real", compare_url)+" e "+link("suíte demo", demo["url"])+"."),
            ("5.5 · Streamlit", "Não implementado. A interface do agente é Vue com FastAPI.")], [.33,.67], size=10)
    p("O "+link("README", REPO+"README.md")+" explica como rodar a demo sem credenciais. Para a defesa, o enunciado também prevê o uso da CLI: "+code(".venv/bin/python -m scripts.cli")+".", size=10.5)
    p("Para gerar este PDF com as dependências instaladas: "+code(".venv/bin/python -m scripts.report")+". O gerador usa as capturas e os resultados salvos; não consulta os serviços nem roda os testes de novo.", size=10.5)
    r.heading("Fontes e uso de IA")
    p(" · ".join([link("Enunciado e rubrica", ASSIGNMENT), link("Artigo ReAct", "https://arxiv.org/abs/2210.03629"),
                  link("Avaliação no LangSmith", "https://docs.langchain.com/langsmith/evaluation-types"),
                  link("Modelo NLI", "https://huggingface.co/cross-encoder/nli-deberta-v3-small"),
                  link("Remotive", "https://github.com/remotive-com/remote-jobs-api"),
                  link("Arbeitnow", "https://www.arbeitnow.com/blog/job-board-api"),
                  link("AwesomeAPI", "https://docs.awesomeapi.com.br/api-de-moedas")]), size=10.3)
    p("OpenAI Codex auxiliou na implementação, nos testes e na redação. Claude Design auxiliou no protótipo e Claude Code na interface Vue e em suas rotas. As figuras de interface são capturas de execuções; as notas vêm dos experimentos identificados.", size=10.3)
    r.end()
    assert r.n == 10
    r.c.save()
    print(PDF)


if __name__ == "__main__":
    render()
