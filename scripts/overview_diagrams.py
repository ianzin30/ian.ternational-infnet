"""Draw the orientation notebook figures and their editable Excalidraw sources."""

import json
from io import BytesIO
from importlib.resources import files

from PIL import Image, ImageDraw, ImageFont

FIGURES = {
    "preparacao-do-curriculo": (
        "Antes da conversa: preparar o índice",
        [
            ("PDF do currículo", "Texto selecionável"),
            ("Docling", "Extrai o texto"),
            ("Trechos", "Mantêm a fonte"),
            ("Embeddings", "Convertem trechos\nem vetores"),
            ("FAISS", "Encontra trechos\nsimilares"),
        ],
    ),
    "salario-da-segunda": (
        "Durante a conversa: resolver “a segunda”",
        [
            ("Pedido", "Converta o salário\nda segunda"),
            ("Sessão", "Encontra o 2º ID\nda última lista"),
            ("Anúncio", "Confere valor, moeda\ne período"),
            ("Cotação", "Busca ou lê a taxa\ne calcula em reais"),
            ("Resposta", "Mostra valores, taxa,\ndata e fonte"),
        ],
    ),
}


def _scene(title, steps):
    width, height, gap, left, top = 196, 115, 24, 28, 80
    specs = [("text", left, 22, 830, 34, title, 28)]
    for i, (label, detail) in enumerate(steps):
        x = left + i * (width + gap)
        specs.extend([
            ("rectangle", x, top, width, height),
            ("text", x + 14, top + 17, width - 28, 24, label, 19),
            ("text", x + 14, top + 54, width - 28, 43, detail, 16),
        ])
        if i < len(steps) - 1:
            specs.append(("arrow", x + width + 3, top + height // 2, gap - 6, 0))
    return specs


def make_diagram(name, destination):
    title, steps = FIGURES[name]
    specs = _scene(title, steps)
    colors = {"paper": "#f4f5ef", "card": "#ffffff", "ink": "#23372d", "line": "#698675"}
    image = Image.new("RGB", (1130 * 2, 220 * 2), colors["paper"])
    draw = ImageDraw.Draw(image)
    elements = []
    for idx, (kind, x, y, w, h, *payload) in enumerate(specs):
        element = {
            "id": f"{name}-{idx}", "type": kind, "x": x, "y": y, "width": w, "height": h,
            "angle": 0, "strokeColor": colors["ink"], "backgroundColor": "transparent",
            "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 0,
            "opacity": 100, "groupIds": [], "frameId": None, "roundness": None, "seed": idx + 1,
            "version": 1, "versionNonce": idx + 1, "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
        }
        a, b, c, d = x * 2, y * 2, (x + w) * 2, (y + h) * 2
        if kind == "rectangle":
            draw.rounded_rectangle((a, b, c, d), radius=18, fill=colors["card"], outline=colors["line"], width=2)
            element.update(backgroundColor=colors["card"], strokeColor=colors["line"], roundness={"type": 3})
        elif kind == "arrow":
            draw.line((a, b, c, b), fill=colors["line"], width=3)
            draw.polygon(((c, b), (c - 12, b - 7), (c - 12, b + 7)), fill=colors["line"])
            element.update(points=[[0, 0], [w, 0]], startBinding=None, endBinding=None,
                           lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow",
                           strokeColor=colors["line"], strokeWidth=2)
        else:
            label, size = payload
            font_name = "VeraBd.ttf" if size >= 19 else "Vera.ttf"
            font_file = files("reportlab").joinpath("fonts", font_name).read_bytes()
            font = ImageFont.truetype(BytesIO(font_file), size * 2)
            while any(draw.textlength(line, font=font) > w * 2 for line in label.splitlines()):
                size -= 1
                if size < 14:
                    raise ValueError(f"Texto comprido para a figura: {label}")
                font = ImageFont.truetype(BytesIO(font_file), size * 2)
            draw.multiline_text((a, b), label, font=font, fill=colors["ink"], spacing=5)
            element.update(text=label, originalText=label, fontSize=size, fontFamily=5,
                           textAlign="left", verticalAlign="top", containerId=None,
                           lineHeight=1.25, autoResize=True)
        elements.append(element)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f"{name}.excalidraw").write_text(json.dumps({
        "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
        "elements": elements, "appState": {"viewBackgroundColor": colors["paper"], "gridSize": 20},
        "files": {},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = BytesIO()
    image.save(result, format="PNG", optimize=True)
    return result.getvalue()
