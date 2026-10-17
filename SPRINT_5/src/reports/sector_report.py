"""Day 34 - sector PDFs: a summary page with median KPIs, then a company directory
listing 8 metrics per company."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from config import settings
from src.analytics.kpi_summary import SECTOR_METRICS, company_kpis, format_value
from src.reports import charts
from src.reports.styles import (ACCENT, BORDER, CONTENT_W, GREY, NAVY, PAGE_H, PAGE_W, ROW_ALT,
                                get_styles)
from src.utils.helpers import safe_filename, soft_break
from src.utils.logger import get_logger

log = get_logger(__name__)


def _draw_page(sector: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - 16 * mm, PAGE_W, 16 * mm, stroke=0, fill=1)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, PAGE_H - 17.2 * mm, PAGE_W, 1.2 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(14 * mm, PAGE_H - 10.5 * mm, f"Sector Report  |  {sector}")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W - 14 * mm, PAGE_H - 10 * mm, settings.PLATFORM_NAME)
        canvas.setStrokeColor(BORDER)
        canvas.line(14 * mm, 12 * mm, PAGE_W - 14 * mm, 12 * mm)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(14 * mm, 8 * mm, f"Generated {date.today():%d %b %Y}  |  Latest available year per company")
        canvas.drawRightString(PAGE_W - 14 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def _sector_table(df: pd.DataFrame, S) -> Table:
    head = [Paragraph("Metric", S["head"])] + [Paragraph(h, S["head_right"]) for h in ("Median", "Min", "Max")]
    rows = [head]
    for key, label, kind in SECTOR_METRICS:
        col = df[key].dropna()
        rows.append([Paragraph(label, S["cell_bold"])] + [
            Paragraph(format_value(kind, fn(col)) if len(col) else "N/A", S["cell_right"])
            for fn in (pd.Series.median, pd.Series.min, pd.Series.max)])
    t = Table(rows, colWidths=[CONTENT_W * 0.40] + [CONTENT_W * 0.20] * 3, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def _directory_table(df: pd.DataFrame, S) -> Table:
    head = [Paragraph("Company", S["head"])] + [Paragraph(label, S["head_right"]) for _, label, _ in SECTOR_METRICS]
    rows = [head]
    for _, r in df.sort_values("ticker").iterrows():
        from xml.sax.saxutils import escape
        name = Paragraph(f"<b>{escape(soft_break(r['company_name']))}</b><br/>"
                         f"<font size='6.5' color='#6B7280'>{escape(soft_break(r['ticker']))}</font>", S["cell"])
        rows.append([name] + [Paragraph(format_value(kind, r[key]), S["cell_right"]) for key, _, kind in SECTOR_METRICS])
    first_w = CONTENT_W * 0.23
    other_w = (CONTENT_W - first_w) / len(SECTOR_METRICS)
    t = Table(rows, colWidths=[first_w] + [other_w] * len(SECTOR_METRICS), repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDER), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def sector_dataframe(store, sector: str) -> pd.DataFrame:
    comps = store.companies[store.companies["sector"] == sector]
    rows = []
    for _, c in comps.iterrows():
        k = company_kpis(store.frame_for(c["company_id"]))
        k.update(company_id=c["company_id"], company_name=c["company_name"], ticker=c["ticker"])
        rows.append(k)
    return pd.DataFrame(rows)


def build_sector_report(store, sector: str, out_path: Path) -> Path:
    S = get_styles()
    df = sector_dataframe(store, sector)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out_path), pagesize=(PAGE_W, PAGE_H), leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=24 * mm, bottomMargin=17 * mm, title=f"Sector Report - {sector}",
                            author=settings.PLATFORM_NAME)
    story: List = [Paragraph(f"{sector} - sector summary", S["title"]),
                   Paragraph(f"{len(df)} companies covered. Medians, minimums and maximums use each company's latest available year.", S["body"]),
                   Spacer(1, 8), Paragraph("Median KPIs", S["section"]),
                   HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=4),
                   _sector_table(df, S), Spacer(1, 10), Paragraph("Return on equity by company", S["section"]),
                   HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=4)]
    ranked = df.dropna(subset=["roe"]).sort_values("roe", ascending=False)
    height = max(130, min(300, 20 * len(ranked) + 40))
    story.append(charts.horizontal_bar(ranked["ticker"].tolist(), ranked["roe"].tolist(),
                                       "ROE (%) - latest year", CONTENT_W - 12, height))
    story += [PageBreak(), Paragraph(f"{sector} - company directory", S["title"]),
              Spacer(1, 4), _directory_table(df, S)]
    doc.build(story, onFirstPage=_draw_page(sector), onLaterPages=_draw_page(sector))
    return out_path


def batch_generate_sector_reports(store, out_dir: Path = settings.SECTOR_DIR) -> List[Path]:
    out_dir = Path(out_dir)
    paths = []
    for sector in sorted(store.companies["sector"].dropna().unique()):
        path = out_dir / f"{safe_filename(sector)}_report.pdf"
        build_sector_report(store, sector, path)
        paths.append(path)
    log.info("Sector reports generated: %d", len(paths))
    return paths
