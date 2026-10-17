"""Day 35 - portfolio summary PDF: one page per company, alphabetical by ticker.

Each page shows company name, sector, the top-6 KPIs and a vector trend arrow:
up (green) = metric improved in the latest year, down (red) = declined,
right (grey) = flat within +/-2 %. Debt/Equity is lower-is-better, so a fall in
D/E is an *improvement* and is shown with an up arrow.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas

from config import settings
from src.analytics.kpi_summary import KPI_DEFS, company_kpis, format_value, trend_direction
from src.reports.styles import (ACCENT, BORDER, GREEN, GREY, LIGHT, NAVY, PAGE_H, PAGE_W, RED,
                                ROW_ALT, draw_trend_arrow, fit_font_size)
from src.utils.helpers import is_nan
from src.utils.logger import get_logger

log = get_logger(__name__)

LEFT, RIGHT = 16 * mm, PAGE_W - 16 * mm


def _change_text(latest, previous) -> str:
    if is_nan(latest) or is_nan(previous):
        return "N/A"
    if previous == 0:
        return "n/m"
    return f"{(latest - previous) / abs(previous) * 100:+.1f}%"


def _draw_page(c, comp, kpis, page_no: int, total: int) -> None:
    name, ticker = str(comp["company_name"]), str(comp["ticker"])
    bar_h = 34 * mm
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.rect(0, PAGE_H - bar_h - 1.5 * mm, PAGE_W, 1.5 * mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    tfont = fit_font_size(c, ticker, "Helvetica-Bold", 60 * mm, 22, 10)
    tw = c.stringWidth(ticker, "Helvetica-Bold", tfont)
    nfont = fit_font_size(c, name, "Helvetica-Bold", RIGHT - LEFT - tw - 10 * mm, 24, 9)
    c.setFont("Helvetica-Bold", nfont)
    c.drawString(LEFT, PAGE_H - 17 * mm, name)
    c.setFont("Helvetica-Bold", tfont)
    c.drawRightString(RIGHT, PAGE_H - 17 * mm, ticker)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#C9D6EA"))
    fy = f"FY{int(kpis['latest_year'])}" if not is_nan(kpis["latest_year"]) else "n/a"
    c.drawString(LEFT, PAGE_H - 26.5 * mm, f"Sector: {comp['sector']}     |     Latest year: {fy}")

    # table header
    y = PAGE_H - bar_h - 14 * mm
    cols = {"kpi": LEFT + 4, "latest": LEFT + 215, "prev": LEFT + 300, "chg": LEFT + 380, "arrow": RIGHT - 14}
    c.setFillColor(NAVY)
    c.rect(LEFT, y - 6, RIGHT - LEFT, 20, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(cols["kpi"], y, "KPI")
    c.drawRightString(cols["latest"] + 60, y, "Latest")
    c.drawRightString(cols["prev"] + 60, y, "Previous")
    c.drawRightString(cols["chg"] + 40, y, "Change")
    c.drawCentredString(cols["arrow"], y, "Trend")

    row_h = 52
    y -= 6
    for i, d in enumerate(KPI_DEFS):
        top = y - i * row_h
        if i % 2 == 0:
            c.setFillColor(ROW_ALT)
            c.rect(LEFT, top - row_h, RIGHT - LEFT, row_h, stroke=0, fill=1)
        c.setStrokeColor(BORDER)
        c.line(LEFT, top - row_h, RIGHT, top - row_h)
        mid = top - row_h / 2
        latest, prev = kpis.get(d.key), kpis.get(d.key + "_prev")
        c.setFillColor(colors.HexColor("#1F2937"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cols["kpi"], mid - 4, d.label)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(cols["latest"] + 60, mid - 5, format_value(d.kind, latest))
        c.setFillColor(GREY)
        c.setFont("Helvetica", 11)
        c.drawRightString(cols["prev"] + 60, mid - 4, format_value(d.kind, prev))
        direction = trend_direction(latest, prev, d.higher_is_better)
        c.setFillColor(GREEN if direction == "up" else RED if direction == "down" else GREY)
        c.setFont("Helvetica", 11)
        c.drawRightString(cols["chg"] + 40, mid - 4, _change_text(latest, prev))
        draw_trend_arrow(c, cols["arrow"], mid, direction, size=14)

    # legend
    ly = y - len(KPI_DEFS) * row_h - 26
    c.setFont("Helvetica", 8)
    x = LEFT
    for direction, text in (("up", "Improved in latest year"), ("down", "Declined in latest year"),
                            ("flat", "Flat (within +/-2%)")):
        draw_trend_arrow(c, x + 5, ly + 3, direction, size=9)
        c.setFillColor(GREY)
        c.drawString(x + 14, ly, text)
        x += 150
    c.setFont("Helvetica-Oblique", 7.5)
    c.drawString(LEFT, ly - 14, "Debt / Equity is lower-is-better: a falling ratio counts as an improvement.")

    # footer
    c.setStrokeColor(BORDER)
    c.line(LEFT, 12 * mm, RIGHT, 12 * mm)
    c.setFillColor(GREY)
    c.setFont("Helvetica", 7)
    c.drawString(LEFT, 8 * mm, f"{settings.PLATFORM_NAME}  |  Portfolio summary  |  Generated {date.today():%d %b %Y}")
    c.drawRightString(RIGHT, 8 * mm, f"Page {page_no} of {total}")


def generate_portfolio_summary(store, out_path: Path = settings.PORTFOLIO_PDF) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    companies = store.companies.sort_values("ticker").reset_index(drop=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Portfolio Summary")
    c.setAuthor(settings.PLATFORM_NAME)
    total = len(companies)
    for i, comp in companies.iterrows():
        kpis = company_kpis(store.frame_for(comp["company_id"]))
        key = f"co_{i}"
        c.bookmarkPage(key)
        c.addOutlineEntry(f"{comp['ticker']} - {comp['company_name']}", key, level=0)
        _draw_page(c, comp, kpis, i + 1, total)
        c.showPage()
    c.save()
    log.info("Portfolio summary written: %d pages", total)
    return out_path
