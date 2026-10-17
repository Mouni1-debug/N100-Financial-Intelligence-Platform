"""Matplotlib chart builders. Each function returns a ReportLab ``Image`` flowable
sized in points, so PDFs always receive pixel-perfect, fixed-size graphics."""
from __future__ import annotations

from io import BytesIO
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # headless / no display needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from reportlab.platypus import Image  # noqa: E402

NAVY, ACCENT, GREEN, RED, AMBER, GREY = "#0B1F3A", "#1F77B4", "#1E8449", "#C0392B", "#E69F00", "#9CA3AF"
DPI = 170


def _fy(year) -> str:
    return f"FY{str(int(year))[-2:]}"


def _finish(fig, width_pt: float, height_pt: float) -> Image:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=DPI)
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_pt, height=height_pt)


def _new_fig(width_pt: float, height_pt: float):
    fig, ax = plt.subplots(figsize=(width_pt / 72, height_pt / 72))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    ax.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    return fig, ax


def _placeholder(title: str, w: float, h: float) -> Image:
    fig, ax = plt.subplots(figsize=(w / 72, h / 72))
    ax.axis("off")
    ax.text(0.5, 0.5, f"{title}\nData not available", ha="center", va="center", fontsize=9, color=GREY)
    return _finish(fig, w, h)


def _series(frame: pd.DataFrame, col: str, n: int = 10) -> pd.Series:
    if frame is None or frame.empty or col not in frame:
        return pd.Series(dtype=float)
    return frame.sort_values("year").set_index("year")[col].dropna().astype(float).iloc[-n:]


def bar_chart(frame: pd.DataFrame, col: str, title: str, w: float, h: float,
              color: str = ACCENT, unit: str = "Rs Cr") -> Image:
    s = _series(frame, col)
    if s.empty:
        return _placeholder(title, w, h)
    fig, ax = _new_fig(w, h)
    colors_ = [color if v >= 0 else RED for v in s.values]
    ax.bar([_fy(y) for y in s.index], s.values, color=colors_, width=0.65)
    ax.set_title(f"{title} ({unit})", fontsize=8.5, fontweight="bold", color=NAVY, loc="left")
    ax.tick_params(axis="x", labelrotation=45)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout()
    return _finish(fig, w, h)


def roe_roce_chart(frame: pd.DataFrame, w: float, h: float) -> Image:
    roe, roce = _series(frame, "roe_pct"), _series(frame, "roce_pct")
    if roe.empty and roce.empty:
        return _placeholder("ROE & ROCE", w, h)
    fig, ax = _new_fig(w, h)
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.tick_params(labelsize=7)
    lines = []
    if not roe.empty:
        lines += ax.plot([_fy(y) for y in roe.index], roe.values, color=ACCENT, marker="o", ms=3.5, lw=1.8, label="ROE (%) - left")
    if not roce.empty:
        lines += ax2.plot([_fy(y) for y in roce.index], roce.values, color=AMBER, marker="s", ms=3.5, lw=1.8, label="ROCE (%) - right")
    ax.set_ylabel("ROE (%)", fontsize=7, color=ACCENT)
    ax2.set_ylabel("ROCE (%)", fontsize=7, color=AMBER)
    ax.set_title("ROE and ROCE trend", fontsize=8.5, fontweight="bold", color=NAVY, loc="left")
    ax.legend(lines, [l.get_label() for l in lines], fontsize=7, frameon=False,
              loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2)
    ax.tick_params(axis="x", labelrotation=0)
    fig.tight_layout()
    return _finish(fig, w, h)


def balance_sheet_chart(frame: pd.DataFrame, w: float, h: float) -> Image:
    if frame is None or frame.empty or "borrowings" not in frame:
        return _placeholder("Balance sheet composition", w, h)
    f = frame.sort_values("year").set_index("year").iloc[-10:]
    equity = (f["equity_capital"].fillna(0) + f["reserves"].fillna(0))
    debt, other = f["borrowings"].fillna(0), f["other_liabilities"].fillna(0)
    if (equity.abs() + debt.abs() + other.abs()).sum() == 0:
        return _placeholder("Balance sheet composition", w, h)
    fig, ax = _new_fig(w, h)
    x = [_fy(y) for y in f.index]
    ax.bar(x, equity, color=NAVY, width=0.65, label="Equity")
    ax.bar(x, debt, bottom=equity, color=AMBER, width=0.65, label="Borrowings")
    ax.bar(x, other, bottom=equity + debt, color=GREY, width=0.65, label="Other liabilities")
    ax.set_title("Balance sheet composition (Rs Cr)", fontsize=8.5, fontweight="bold", color=NAVY, loc="left")
    ax.set_ylim(0, float((equity + debt + other).max()) * 1.2)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", ncol=3)
    ax.tick_params(axis="x", labelrotation=45)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout()
    return _finish(fig, w, h)


def cashflow_waterfall(frame: pd.DataFrame, w: float, h: float) -> Image:
    if frame is None or frame.empty:
        return _placeholder("Cash flow waterfall", w, h)
    f = frame.sort_values("year")
    last = f.iloc[-1]
    cfo, cfi, cff = (last.get("operating_activity"), last.get("investing_activity"), last.get("financing_activity"))
    if any(pd.isna(v) for v in (cfo, cfi, cff)):
        return _placeholder("Cash flow waterfall", w, h)
    net = last.get("net_cash_flow")
    net = cfo + cfi + cff if pd.isna(net) else net
    fig, ax = _new_fig(w, h)
    labels = ["CFO", "CFI", "CFF", "Net cash flow"]
    bottoms = [0, cfo, cfo + cfi, 0]
    heights = [cfo, cfi, cff, net]
    spans = [(b, b + v) for b, v in zip(bottoms, heights)]
    low, high = min(0, *(lo for pair in spans for lo in pair)), max(0, *(hi for pair in spans for hi in pair))
    pad = (high - low) * 0.16 or 1.0
    for i, (b, v) in enumerate(zip(bottoms, heights)):
        color = NAVY if i == 3 else (GREEN if v >= 0 else RED)
        ax.bar(labels[i], v, bottom=b, color=color, width=0.6)
        ax.text(i, b + v + (pad * 0.12 if v >= 0 else -pad * 0.12), f"{v:,.0f}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=7, color=NAVY)
    ax.axhline(0, color="#374151", lw=0.8)
    ax.set_ylim(low - pad, high + pad)
    ax.set_title(f"Cash flow waterfall - {_fy(last['year'])} (Rs Cr)", fontsize=8.5, fontweight="bold", color=NAVY, loc="left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout()
    return _finish(fig, w, h)


def horizontal_bar(labels, values, title: str, w: float, h: float, color: str = ACCENT) -> Image:
    if not len(labels):
        return _placeholder(title, w, h)
    fig, ax = plt.subplots(figsize=(w / 72, h / 72))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=7)
    cols = [color if (v is not None and v == v and v >= 0) else RED for v in values]
    ys = range(len(labels))
    ax.barh(list(ys), [0 if v != v else v for v in values], color=cols, height=0.6)
    ax.set_yticks(list(ys))
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=8.5, fontweight="bold", color=NAVY, loc="left")
    ax.grid(axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return _finish(fig, w, h)
