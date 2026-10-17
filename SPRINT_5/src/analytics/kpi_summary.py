"""Shared KPI definitions + latest/previous value extraction used by all reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd

from config import settings
from src.utils.helpers import NAN, cagr_pct, is_nan


@dataclass(frozen=True)
class KpiDef:
    key: str
    label: str
    column: str
    kind: str                # money | pct | ratio
    higher_is_better: bool


# The six headline KPIs (tearsheet tiles and portfolio summary rows).
KPI_DEFS = (
    KpiDef("revenue", "Revenue (Rs Cr)", "sales", "money", True),
    KpiDef("net_profit", "Net Profit (Rs Cr)", "net_profit", "money", True),
    KpiDef("opm", "Operating Margin (%)", "opm_pct", "pct", True),
    KpiDef("roe", "ROE (%)", "roe_pct", "pct", True),
    KpiDef("roce", "ROCE (%)", "roce_pct", "pct", True),
    KpiDef("de", "Debt / Equity (x)", "de_ratio", "ratio", False),
)

# The eight metrics shown per company on sector reports: (key, label, kind)
SECTOR_METRICS = (
    ("revenue", "Revenue (Rs Cr)", "money"),
    ("net_profit", "Net Profit (Rs Cr)", "money"),
    ("opm", "OPM (%)", "pct"),
    ("roe", "ROE (%)", "pct"),
    ("roce", "ROCE (%)", "pct"),
    ("de", "D/E (x)", "ratio"),
    ("sales_cagr_5", "Sales CAGR 5Y (%)", "pct"),
    ("pat_cagr_5", "PAT CAGR 5Y (%)", "pct"),
)


def format_value(kind: str, value) -> str:
    if is_nan(value):
        return "N/A"
    if kind == "money":
        return f"{value:,.0f}"
    if kind == "pct":
        return f"{value:.1f}%"
    return f"{value:.2f}x"


def trend_direction(latest, previous, higher_is_better: bool,
                    flat_tolerance_pct: float = settings.FLAT_TOLERANCE_PCT):
    """Return 'up' (improved), 'down' (declined), 'flat' (within tolerance) or None.

    'Improved' respects the metric's polarity: a falling Debt/Equity is an
    improvement and therefore returns 'up'.
    """
    if is_nan(latest) or is_nan(previous):
        return None
    if previous == 0:
        rel_pct = 0.0 if latest == 0 else float("inf")
    else:
        rel_pct = abs((latest - previous) / abs(previous)) * 100.0
    if rel_pct <= flat_tolerance_pct:
        return "flat"
    improved = latest > previous if higher_is_better else latest < previous
    return "up" if improved else "down"


def company_kpis(frame: pd.DataFrame) -> Dict[str, float]:
    """Latest-year KPI values (+ previous year and 5Y CAGRs) for one company."""
    out: Dict[str, float] = {"latest_year": NAN, "n_years": 0}
    if frame is None or frame.empty:
        for d in KPI_DEFS:
            out[d.key] = NAN
            out[d.key + "_prev"] = NAN
        out.update(sales_cagr_5=NAN, pat_cagr_5=NAN, eps_cagr_5=NAN)
        return out
    f = frame.sort_values("year").set_index("year")
    ly = int(f.index.max())
    out["latest_year"] = ly
    out["n_years"] = int(f["sales"].notna().sum())
    for d in KPI_DEFS:
        col = f[d.column] if d.column in f else pd.Series(dtype=float)
        out[d.key] = float(col.get(ly, NAN))
        out[d.key + "_prev"] = float(col.get(ly - 1, NAN))

    def _cagr(col: str) -> float:
        if col not in f or (ly - 5) not in f.index:
            return NAN
        return cagr_pct(f[col].get(ly - 5, NAN), f[col].get(ly, NAN), 5)

    out["sales_cagr_5"] = _cagr("sales")
    out["pat_cagr_5"] = _cagr("net_profit")
    out["eps_cagr_5"] = _cagr("eps")
    return out
