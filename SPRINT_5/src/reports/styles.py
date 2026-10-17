"""Shared ReportLab styles, colours and small custom flowables."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable

PAGE_W, PAGE_H = A4
MARGIN_X = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

NAVY = colors.HexColor("#0B1F3A")
ACCENT = colors.HexColor("#1F77B4")
TEAL = colors.HexColor("#17A2B8")
GREEN = colors.HexColor("#1E8449")
GREEN_BG = colors.HexColor("#EAF6EE")
RED = colors.HexColor("#C0392B")
RED_BG = colors.HexColor("#FBEDEC")
AMBER = colors.HexColor("#E69F00")
GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#F1F4F9")
ROW_ALT = colors.HexColor("#F7F9FC")
BORDER = colors.HexColor("#D0D5DD")

# Badge colour per capital-allocation pattern (unknown patterns fall back to grey).
PATTERN_COLORS = {
    "Reinvestor": colors.HexColor("#1F77B4"),
    "Aggressive Expander": colors.HexColor("#6F42C1"),
    "Asset Monetizer": colors.HexColor("#17A2B8"),
    "Cash Accumulator": colors.HexColor("#1E8449"),
    "Capital Raiser": colors.HexColor("#E69F00"),
    "Cash Burner": colors.HexColor("#D35400"),
    "Distress Signal": colors.HexColor("#C0392B"),
    "Asset Liquidator": colors.HexColor("#7F8C8D"),
}


def _style(name: str, **kw) -> ParagraphStyle:
    base = dict(fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#1F2937"),
                alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)


def get_styles() -> dict:
    """Paragraph styles. Every table cell is a Paragraph (which word-wraps inside its
    column); very long unbroken tokens are pre-split with ``helpers.soft_break``."""
    return {
        "section": _style("section", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=NAVY,
                          spaceBefore=6, spaceAfter=3),
        "body": _style("body"),
        "small": _style("small", fontSize=7.5, leading=10, textColor=GREY),
        "note": _style("note", fontName="Helvetica-Oblique", fontSize=8.5, textColor=GREY),
        "kpi_label": _style("kpi_label", fontSize=7.5, leading=9, textColor=GREY),
        "kpi_value": _style("kpi_value", fontName="Helvetica-Bold", fontSize=17, leading=21,
                            textColor=NAVY),
        "cell": _style("cell", fontSize=8, leading=10),
        "cell_bold": _style("cell_bold", fontName="Helvetica-Bold", fontSize=8, leading=10),
        "cell_right": _style("cell_right", fontSize=8, leading=10, alignment=2),
        "head": _style("head", fontName="Helvetica-Bold", fontSize=7.5, leading=9,
                       textColor=colors.white),
        "head_right": _style("head_right", fontName="Helvetica-Bold", fontSize=7.5, leading=9,
                             textColor=colors.white, alignment=2),
        "bullet": _style("bullet", fontSize=8.5, leading=11.5, leftIndent=11, firstLineIndent=-11,
                         spaceAfter=3),
        "title": _style("title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=NAVY),
    }


class Badge(Flowable):
    """Rounded coloured badge, e.g. the capital-allocation pattern."""

    def __init__(self, text: str, color, width: float = 170, height: float = 24) -> None:
        super().__init__()
        self.text, self.color, self.width, self.height = text, color, width, height

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0, self.width, self.height, 6, stroke=0, fill=1)
        c.setFillColor(colors.white)
        size = 11
        while c.stringWidth(self.text, "Helvetica-Bold", size) > self.width - 12 and size > 6:
            size -= 0.5
        c.setFont("Helvetica-Bold", size)
        c.drawCentredString(self.width / 2, self.height / 2 - size * 0.35, self.text)


def fit_font_size(canvas, text: str, font: str, max_width: float, start: float, minimum: float = 8) -> float:
    """Largest font size (<= start) at which ``text`` fits ``max_width``."""
    size = start
    while canvas.stringWidth(text, font, size) > max_width and size > minimum:
        size -= 0.5
    return size


def draw_trend_arrow(canvas, x: float, y: float, direction, size: float = 11) -> None:
    """Vector arrow (no font glyphs needed). Up = improved (green), down = declined (red),
    right = flat (grey). ``x, y`` is the arrow's centre."""
    canvas.saveState()
    h = size / 2
    if direction == "up":
        canvas.setFillColor(GREEN)
        p = canvas.beginPath(); p.moveTo(x, y + h); p.lineTo(x + h, y - h); p.lineTo(x - h, y - h); p.close()
    elif direction == "down":
        canvas.setFillColor(RED)
        p = canvas.beginPath(); p.moveTo(x, y - h); p.lineTo(x + h, y + h); p.lineTo(x - h, y + h); p.close()
    elif direction == "flat":
        canvas.setFillColor(GREY)
        p = canvas.beginPath(); p.moveTo(x + h, y); p.lineTo(x - h, y + h); p.lineTo(x - h, y - h); p.close()
    else:
        canvas.setFillColor(BORDER)
        canvas.rect(x - h * 0.6, y - 1, h * 1.2, 2, stroke=0, fill=1)
        canvas.restoreState()
        return
    canvas.drawPath(p, stroke=0, fill=1)
    canvas.restoreState()
