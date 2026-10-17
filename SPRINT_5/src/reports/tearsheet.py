"""Day 33/34 - two-page company tearsheet (ReportLab).

Page 1: navy header bar, 6 KPI tiles (2 x 3), Revenue and Net Profit bar charts
        side by side, ROE / ROCE dual-axis line chart.
Page 2: balance-sheet composition (stacked), cash-flow waterfall, pros (green),
        cons (red) and the capital-allocation badge.

Overflow protection
-------------------
* every table cell is a Paragraph (word-wrap) with explicit column widths, and long
  unbroken tokens are pre-split by ``soft_break``,
* each page body is wrapped in ``KeepInFrame(mode='shrink')`` so it can never spill
  onto a third page - the shrink factor is logged if it becomes noticeable.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, KeepInFrame, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from config import settings
from src.analytics.kpi_summary import KPI_DEFS, company_kpis, format_value
from src.reports import charts
from src.reports.styles import (ACCENT, BORDER, CONTENT_W, GREEN, GREEN_BG, GREY, LIGHT, NAVY,
                                PAGE_H, PAGE_W, PATTERN_COLORS, RED, RED_BG, Badge, fit_font_size,
                                get_styles)
from src.utils.helpers import is_nan, safe_filename, soft_break
from src.utils.logger import get_logger

log = get_logger(__name__)

MAX_STATEMENTS = 6
SHRINK_WARN = 0.85
_PAD = 6  # SimpleDocTemplate frame padding (points)


class FittedPage(KeepInFrame):
    """KeepInFrame(mode='shrink') that remembers how much it had to shrink."""

    shrink_factor = 1.0

    def wrap(self, availWidth, availHeight):
        result = super().wrap(availWidth, availHeight)
        scale = getattr(self, "_scale", 1.0) or 1.0
        self.shrink_factor = 1.0 / scale if scale > 1 else 1.0
        return result


# --------------------------------------------------------------------------- #
# Page furniture (drawn on the canvas)
# --------------------------------------------------------------------------- #
def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(14 * mm, 12 * mm, PAGE_W - 14 * mm, 12 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    canvas.drawString(14 * mm, 8 * mm,
                      f"{settings.PLATFORM_NAME}  |  Generated {date.today():%d %b %Y}  |  "
                      "For information only - not investment advice.")
    canvas.drawRightString(PAGE_W - 14 * mm, 8 * mm, f"Page {doc.page} of 2")
    canvas.restoreState()


def _header(company: pd.Series, first: bool):
    def draw(canvas, doc):
        canvas.saveState()
        bar_h = 24 * mm if first else 12 * mm
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - bar_h, PAGE_W, bar_h, stroke=0, fill=1)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, PAGE_H - bar_h - 1.2 * mm, PAGE_W, 1.2 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        name, ticker = str(company["company_name"]), str(company["ticker"])
        ticker_font = 18 if first else 11
        tw = canvas.stringWidth(ticker, "Helvetica-Bold", ticker_font)
        max_name_w = PAGE_W - 28 * mm - tw - 12 * mm
        name_font = fit_font_size(canvas, name, "Helvetica-Bold", max_name_w, 21 if first else 13, 8)
        canvas.setFont("Helvetica-Bold", name_font)
        canvas.drawString(14 * mm, PAGE_H - bar_h / 2 - (3 if not first else 0) - name_font * 0.1,
                          name)
        canvas.setFont("Helvetica-Bold", ticker_font)
        canvas.drawRightString(PAGE_W - 14 * mm, PAGE_H - bar_h / 2 - (2 if not first else -1), ticker)
        if first:
            canvas.setFont("Helvetica", 9)
            canvas.setFillColor(colors.HexColor("#C9D6EA"))
            canvas.drawString(14 * mm, PAGE_H - bar_h + 5 * mm, f"Sector: {company['sector']}")
        _footer(canvas, doc)
        canvas.restoreState()
    return draw


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def _section(title: str, S) -> list:
    return [Paragraph(title, S["section"]),
            HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=4)]


def _kpi_tiles(kpis: Dict, S, width: float) -> Table:
    cells = []
    for d in KPI_DEFS:
        cells.append([Paragraph(d.label, S["kpi_label"]),
                      Paragraph(format_value(d.kind, kpis.get(d.key)), S["kpi_value"])])
    col_w = width / 3
    table = Table([cells[0:3], cells[3:6]], colWidths=[col_w] * 3, rowHeights=[48, 48])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEABOVE", (0, 0), (-1, -1), 2, ACCENT),
        ("LINEAFTER", (0, 0), (1, -1), 6, colors.white),
        ("LINEBELOW", (0, 0), (-1, 0), 6, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _side_by_side(left, right, width: float) -> Table:
    t = Table([[left, right]], colWidths=[width / 2, width / 2])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


def _statement_box(items: List[Tuple[str, float]], color, bg, S, width: float, empty_text: str) -> Table:
    if items:
        paras = [Paragraph(
            f'<font color="{color.hexval().replace("0x", "#")}"><b>&bull;</b></font>&nbsp;&nbsp;'
            f'{escape(soft_break(text))} <font size="7" color="#6B7280">({conf:.0f}%)</font>', S["bullet"])
            for text, conf in items]
    else:
        paras = [Paragraph(empty_text, S["note"])]
    box = Table([[paras]], colWidths=[width])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return box


def _cashflow_chips(cf: Dict, S, width: float) -> Table:
    """Four small facts from the Day 31 module (all cells wrap)."""
    score = cf.get("cfo_quality_score")
    capex = cf.get("capex_intensity_pct")
    facts = [
        ("CFO quality", f"{cf.get('cfo_quality_label', 'N/A')}" + (f" ({score:.2f})" if not is_nan(score) else "")),
        ("CapEx intensity", f"{cf.get('capex_label', 'N/A')}" + (f" ({capex:.1f}%)" if not is_nan(capex) else "")),
        ("Distress signal", "Yes - CFO < 0 and CFF > 0" if cf.get("distress_flag") else "No"),
        ("Deleveraging", "Yes - repaying debt" if cf.get("deleveraging_flag") else "No"),
    ]
    cells = [[Paragraph(label, S["kpi_label"]), Paragraph(f"<b>{escape(soft_break(value))}</b>", S["cell"])] for label, value in facts]
    t = Table([cells], colWidths=[width / 4] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEAFTER", (0, 0), (-2, -1), 5, colors.white),
        ("LINEABOVE", (0, 0), (-1, -1), 2, RED if cf.get("distress_flag") else ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def build_tearsheet(company: pd.Series, frame: pd.DataFrame,
                    pros: Iterable[Tuple[str, float]], cons: Iterable[Tuple[str, float]],
                    allocation_label: Optional[str], out_path: Path,
                    cashflow: Optional[Dict] = None) -> Dict:
    """Render one two-page tearsheet and return ``{'path', 'shrink'}``."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    S = get_styles()
    pros, cons = list(pros)[:MAX_STATEMENTS], list(cons)[:MAX_STATEMENTS]
    kpis = company_kpis(frame)
    fy = f"FY{int(kpis['latest_year'])}" if not is_nan(kpis["latest_year"]) else "latest year"

    doc = SimpleDocTemplate(
        str(out_path), pagesize=(PAGE_W, PAGE_H), leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=31 * mm, bottomMargin=17 * mm,
        title=f"{company['company_name']} - Tearsheet", author=settings.PLATFORM_NAME,
        subject=f"{company['ticker']} company tearsheet")
    body_w = doc.width - 2 * _PAD
    body_h = doc.height - 2 * _PAD - 2
    half_w = body_w / 2

    # ---- page 1 -------------------------------------------------------- #
    page1 = []
    page1 += _section(f"Key performance indicators ({fy})", S)
    page1.append(_kpi_tiles(kpis, S, body_w))
    page1.append(Spacer(1, 6))
    page1 += _section("10-year Revenue and Net Profit", S)
    page1.append(_side_by_side(
        charts.bar_chart(frame, "sales", "Revenue", half_w - 4, 190, charts.ACCENT),
        charts.bar_chart(frame, "net_profit", "Net Profit", half_w - 4, 190, charts.GREEN), body_w))
    page1.append(Spacer(1, 6))
    page1 += _section("Return ratios (ROE and ROCE)", S)
    page1.append(charts.roe_roce_chart(frame, body_w, 250))
    p1 = FittedPage(body_w, body_h, page1, mode="shrink", name="page1")

    # ---- page 2 -------------------------------------------------------- #
    page2 = []
    page2 += _section("Balance sheet composition and cash flow", S)
    page2.append(_side_by_side(
        charts.balance_sheet_chart(frame, half_w - 4, 215),
        charts.cashflow_waterfall(frame, half_w - 4, 215), body_w))
    page2.append(Spacer(1, 4))
    page2 += _section("Pros - what the numbers favour", S)
    page2.append(_statement_box(pros, GREEN, GREEN_BG, S, body_w, "No pro signal above the confidence threshold."))
    page2.append(Spacer(1, 4))
    page2 += _section("Cons - what to watch", S)
    page2.append(_statement_box(cons, RED, RED_BG, S, body_w, "No con signal above the confidence threshold."))
    page2.append(Spacer(1, 4))
    page2 += _section(f"Capital allocation pattern ({fy})", S)
    label = allocation_label or "Not Available"
    page2.append(Badge(label, PATTERN_COLORS.get(label, GREY), width=185, height=24))
    if cashflow:
        page2.append(Spacer(1, 4))
        page2 += _section("Cash flow intelligence", S)
        page2.append(_cashflow_chips(cashflow, S, body_w))
    p2 = FittedPage(body_w, body_h, page2, mode="shrink", name="page2")

    first, later = _header(company, True), _header(company, False)
    doc.build([p1, PageBreak(), p2], onFirstPage=first, onLaterPages=later)

    shrink = min(p1.shrink_factor, p2.shrink_factor)
    if shrink < SHRINK_WARN:
        log.warning("%s: page content shrunk to %.0f%% to fit - review layout", company["ticker"], shrink * 100)
    return {"path": out_path, "shrink": shrink}


def statements_for(pros_cons: pd.DataFrame, company_id) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    sub = pros_cons[pros_cons["company_id"] == company_id].sort_values("confidence_pct", ascending=False)
    pros = [(r.text, r.confidence_pct) for r in sub[sub["type"] == "pro"].itertuples()]
    cons = [(r.text, r.confidence_pct) for r in sub[sub["type"] == "con"].itertuples()]
    return pros, cons


def batch_generate(store, pros_cons: pd.DataFrame, allocation: Dict,
                   out_dir: Path = settings.TEARSHEET_DIR, tickers: Optional[List[str]] = None,
                   skipped_csv: Optional[Path] = settings.SKIPPED_TEARSHEETS_CSV) -> Tuple[List[Dict], pd.DataFrame]:
    """Generate tearsheets; companies with < 3 years of data are skipped and logged."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    companies = store.companies.sort_values("ticker")
    if tickers:
        companies = companies[companies["ticker"].isin(tickers)]
    results, skipped = [], []
    from src.analytics.cashflow_kpis import compute_cashflow_kpis
    cashflow = compute_cashflow_kpis(store, allocation).set_index("company_id").to_dict("index")
    for _, comp in companies.iterrows():
        years = store.years_available(comp["company_id"])
        if years < settings.MIN_YEARS_FOR_TEARSHEET:
            skipped.append({"company_id": comp["company_id"], "ticker": comp["ticker"],
                            "years_available": years, "reason": f"fewer than {settings.MIN_YEARS_FOR_TEARSHEET} years of data"})
            log.warning("Skipping %s: only %d year(s) of data", comp["ticker"], years)
            continue
        pros, cons = statements_for(pros_cons, comp["company_id"])
        path = out_dir / f"{safe_filename(comp['ticker'])}_tearsheet.pdf"
        try:
            res = build_tearsheet(comp, store.frame_for(comp["company_id"]), pros, cons,
                                  allocation.get(comp["company_id"]), path,
                                  cashflow.get(comp["company_id"]))
            res["ticker"] = comp["ticker"]
            results.append(res)
        except Exception as exc:
            log.exception("Tearsheet failed for %s", comp["ticker"])
            skipped.append({"company_id": comp["company_id"], "ticker": comp["ticker"],
                            "years_available": years, "reason": f"error: {exc}"})
    skipped_df = pd.DataFrame(skipped, columns=["company_id", "ticker", "years_available", "reason"])
    if skipped_csv is not None:
        skipped_df.to_csv(skipped_csv, index=False)
    log.info("Tearsheets: %d generated, %d skipped", len(results), len(skipped_df))
    return results, skipped_df
