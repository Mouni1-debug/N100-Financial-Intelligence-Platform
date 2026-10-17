"""Day 30 - Automatic pros / cons generator.

Implements 12 pro rules and 12 con rules. Every rule returns a ``Signal`` with a
*strength* in [0, 1] (how far beyond its threshold the company is) and a
*coverage* in [0, 1] (how complete the data window was). Confidence is::

    confidence_pct = (60 + 40 * strength) * coverage

Only signals with confidence strictly above ``CONFIDENCE_THRESHOLD`` (60) are
written. Companies that end up without a pro or a con receive a clearly marked
sector-relative fallback statement (rule_id ``PRO_FB`` / ``CON_FB``) so the
"at least one pro and one con per company" rule always holds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from config import settings
from src.analytics.kpi_summary import company_kpis
from src.utils.data_loader import DataStore
from src.utils.helpers import (NAN, cagr_pct, clip01, is_nan, strict_trend,
                               trailing_streak)
from src.utils.logger import get_logger

log = get_logger(__name__)

OUTPUT_COLUMNS = ["company_id", "type", "rule_id", "text", "confidence_pct"]


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Signal:
    strength: float
    coverage: float = 1.0
    fmt: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Rule:
    rule_id: str
    kind: str                     # "pro" | "con"
    description: str
    text: str                     # may contain {x}-style placeholders filled from Signal.fmt
    evaluate: Callable[["CompanyContext"], Optional[Signal]]
    non_financial_only: bool = False


class CompanyContext:
    """Convenience wrapper around one company's yearly fundamentals."""

    def __init__(self, company: pd.Series, frame: pd.DataFrame) -> None:
        self.company_id = company["company_id"]
        self.ticker = company["ticker"]
        self.sector = company["sector"]
        self.is_financial = bool(company["is_financial"])
        self.frame = frame.sort_values("year").set_index("year") if len(frame) else frame
        self.latest_year = int(self.frame.index.max()) if len(self.frame) else None

    def series(self, col: str, n: Optional[int] = None) -> pd.Series:
        if self.latest_year is None or col not in self.frame:
            return pd.Series(dtype=float)
        s = self.frame[col].dropna().astype(float)
        return s.iloc[-n:] if n else s

    def latest(self, col: str) -> float:
        if self.latest_year is None or col not in self.frame:
            return NAN
        return float(self.frame[col].get(self.latest_year, NAN))

    def cagr(self, col: str, years: int = 5) -> float:
        if self.latest_year is None or col not in self.frame:
            return NAN
        start = self.latest_year - years
        if start not in self.frame.index:
            return NAN
        return cagr_pct(self.frame[col].get(start, NAN), self.frame[col].get(self.latest_year, NAN), years)

    def coverage(self, col: str, window: int) -> float:
        if self.latest_year is None or col not in self.frame:
            return 0.0
        present = sum(1 for y in range(self.latest_year - window + 1, self.latest_year + 1)
                      if y in self.frame.index and pd.notna(self.frame[col].get(y)))
        return present / window


# --------------------------------------------------------------------------- #
# Pro rules
# --------------------------------------------------------------------------- #
def p1_roe_sustained(c: CompanyContext) -> Optional[Signal]:
    roe = c.series("roe_pct")
    streak = trailing_streak(roe, lambda v: v > 20)
    if streak < 3:
        return None
    strength = 0.5 * clip01((roe.iloc[-streak:].min() - 20) / 15) + 0.5 * clip01((streak - 3) / 5)
    return Signal(strength, c.coverage("roe_pct", 3))


def p2_fcf_positive_streak(c: CompanyContext) -> Optional[Signal]:
    streak = trailing_streak(c.series("fcf"), lambda v: v > 0)
    if streak < 5:
        return None
    return Signal(0.4 + 0.6 * clip01((streak - 5) / 5), c.coverage("fcf", 5))


def p3_debt_free(c: CompanyContext) -> Optional[Signal]:
    de = c.latest("de_ratio")
    return Signal(1.0) if not is_nan(de) and de <= 0.001 else None


def p4_revenue_cagr(c: CompanyContext) -> Optional[Signal]:
    v = c.cagr("sales")
    return Signal(clip01((v - 15) / 15)) if not is_nan(v) and v > 15 else None


def p5_high_opm(c: CompanyContext) -> Optional[Signal]:
    v = c.latest("opm_pct")
    return Signal(clip01((v - 25) / 20)) if not is_nan(v) and v > 25 else None


def p6_pat_cagr(c: CompanyContext) -> Optional[Signal]:
    v = c.cagr("net_profit")
    return Signal(clip01((v - 20) / 20)) if not is_nan(v) and v > 20 else None


def p7_high_icr(c: CompanyContext) -> Optional[Signal]:
    de, icr = c.latest("de_ratio"), c.latest("icr")
    if not is_nan(de) and de <= 0.001:
        return Signal(1.0)
    if not is_nan(icr) and icr > 10:
        return Signal(clip01((icr - 10) / 20))
    return None


def p8_dividend_with_fcf(c: CompanyContext) -> Optional[Signal]:
    dy, fcf = c.latest("dividend_yield_pct"), c.latest("fcf")
    if not is_nan(dy) and not is_nan(fcf) and dy > 2 and fcf > 0:
        return Signal(clip01((dy - 2) / 3))
    return None


def p9_eps_cagr(c: CompanyContext) -> Optional[Signal]:
    v = c.cagr("eps")
    return Signal(clip01((v - 15) / 15)) if not is_nan(v) and v > 15 else None


def p10_roe_improving(c: CompanyContext) -> Optional[Signal]:
    roe = c.series("roe_pct")
    if not strict_trend(roe, 3, "up"):
        return None
    return Signal(clip01((roe.iloc[-1] - roe.iloc[-4]) / 10), c.coverage("roe_pct", 4))


def p11_operating_leverage(c: CompanyContext) -> Optional[Signal]:
    # Spec title says "Revenue CAGR > PAT CAGR" but the spec TEXT describes profits
    # growing faster than revenue (operating leverage); the text is implemented.
    rev, pat = c.cagr("sales"), c.cagr("net_profit")
    if is_nan(rev) or is_nan(pat) or rev <= 0 or pat <= rev:
        return None
    return Signal(clip01((pat - rev) / 15))


def p12_assets_up_debt_down(c: CompanyContext) -> Optional[Signal]:
    assets, debt = c.series("total_assets", 4), c.series("borrowings", 4)
    if len(assets) < 4 or len(debt) < 4 or not strict_trend(assets, 3, "up"):
        return None
    if debt.iloc[0] <= 0 or debt.iloc[-1] >= debt.iloc[0] or debt.iloc[-1] > debt.iloc[-2]:
        return None
    asset_cagr = cagr_pct(assets.iloc[0], assets.iloc[-1], 3)
    debt_drop = (debt.iloc[0] - debt.iloc[-1]) / debt.iloc[0]
    return Signal(0.5 * clip01(asset_cagr / 15) + 0.5 * clip01(debt_drop / 0.3), c.coverage("total_assets", 4))


# --------------------------------------------------------------------------- #
# Con rules
# --------------------------------------------------------------------------- #
def c1_high_de(c: CompanyContext) -> Optional[Signal]:
    de = c.latest("de_ratio")
    return Signal(clip01((de - 2) / 3), fmt={"x": de}) if not is_nan(de) and de > 2.0 else None


def c2_fcf_negative(c: CompanyContext) -> Optional[Signal]:
    streak = trailing_streak(c.series("fcf"), lambda v: v < 0)
    if streak < 3:
        return None
    return Signal(0.4 + 0.6 * clip01((streak - 3) / 3), c.coverage("fcf", 3))


def c3_opm_declining(c: CompanyContext) -> Optional[Signal]:
    opm = c.series("opm_pct")
    if not strict_trend(opm, 3, "down"):
        return None
    return Signal(clip01((opm.iloc[-4] - opm.iloc[-1]) / 10), c.coverage("opm_pct", 4))


def c4_net_loss(c: CompanyContext) -> Optional[Signal]:
    np_, sales = c.latest("net_profit"), c.latest("sales")
    if is_nan(np_) or np_ >= 0:
        return None
    size = abs(np_) / sales / 0.10 if not is_nan(sales) and sales > 0 else 0.5
    return Signal(0.7 + 0.3 * clip01(size))


def c5_revenue_decline(c: CompanyContext) -> Optional[Signal]:
    sales = c.series("sales")
    streak = trailing_streak(sales.diff().dropna(), lambda d: d < 0)
    if streak < 2:
        return None
    base = sales.iloc[-streak - 1]
    decline_pct = (base - sales.iloc[-1]) / base * 100 if base > 0 else 0.0
    return Signal(0.3 + 0.7 * clip01(decline_pct / 20), c.coverage("sales", 3))


def c6_low_icr(c: CompanyContext) -> Optional[Signal]:
    icr, de = c.latest("icr"), c.latest("de_ratio")
    if is_nan(icr) or icr >= 1.5 or (not is_nan(de) and de <= 0.001):
        return None
    return Signal(clip01((1.5 - icr) / 1.5))


def c7_payout_over_100(c: CompanyContext) -> Optional[Signal]:
    v = c.latest("dividend_payout_pct")
    return Signal(clip01((v - 100) / 100)) if not is_nan(v) and v > 100 else None


def c8_de_rising(c: CompanyContext) -> Optional[Signal]:
    de = c.series("de_ratio")
    if not strict_trend(de, 3, "up"):
        return None
    return Signal(clip01((de.iloc[-1] - de.iloc[-4]) / 1.5), c.coverage("de_ratio", 4))


def c9_eps_declining(c: CompanyContext) -> Optional[Signal]:
    eps = c.series("eps")
    if not strict_trend(eps, 3, "down"):
        return None
    start = eps.iloc[-4]
    drop = (start - eps.iloc[-1]) / abs(start) / 0.5 if start != 0 else 0.5
    return Signal(clip01(drop), c.coverage("eps", 4))


def c10_low_roce(c: CompanyContext) -> Optional[Signal]:
    v = c.latest("roce_pct")
    return Signal(clip01((10 - v) / 10)) if not is_nan(v) and v < 10 else None


def c11_net_debt_ebitda(c: CompanyContext) -> Optional[Signal]:
    nd, ebitda = c.latest("net_debt"), c.latest("ebitda")
    if is_nan(nd) or is_nan(ebitda) or ebitda <= 0 or nd <= 0:
        return None
    ratio = nd / ebitda
    return Signal(clip01((ratio - 3) / 3)) if ratio > 3 else None


def c12_low_revenue_cagr(c: CompanyContext) -> Optional[Signal]:
    v = c.cagr("sales")
    return Signal(clip01((5 - v) / 10)) if not is_nan(v) and v < 5 else None


# --------------------------------------------------------------------------- #
# Rule registry (texts are taken verbatim from the sprint specification)
# --------------------------------------------------------------------------- #
RULES: List[Rule] = [
    Rule("PRO_01", "pro", "ROE > 20% sustained for 3+ years",
         "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
         p1_roe_sustained),
    Rule("PRO_02", "pro", "FCF positive for 5+ consecutive years",
         "Strong free cash flow generation over 5 years signals healthy business fundamentals",
         p2_fcf_positive_streak),
    Rule("PRO_03", "pro", "D/E = 0 in latest year",
         "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
         p3_debt_free, non_financial_only=True),
    Rule("PRO_04", "pro", "Revenue CAGR > 15% over 5 years",
         "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
         p4_revenue_cagr),
    Rule("PRO_05", "pro", "OPM > 25% in latest year",
         "Operating profit margin above 25% indicates strong pricing power and cost discipline",
         p5_high_opm, non_financial_only=True),
    Rule("PRO_06", "pro", "PAT CAGR > 20% over 5 years",
         "Net profit compounding at above 20% over 5 years creates significant shareholder value",
         p6_pat_cagr),
    Rule("PRO_07", "pro", "ICR > 10 or debt free",
         "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
         p7_high_icr, non_financial_only=True),
    Rule("PRO_08", "pro", "Dividend yield > 2% with FCF positive",
         "Consistent dividend yield above 2% backed by positive free cash flow",
         p8_dividend_with_fcf),
    Rule("PRO_09", "pro", "EPS CAGR > 15% over 5 years",
         "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
         p9_eps_cagr),
    Rule("PRO_10", "pro", "ROE improving for 3 consecutive years",
         "Return on equity improving for 3 consecutive years shows strengthening business quality",
         p10_roe_improving),
    Rule("PRO_11", "pro", "Profit CAGR outpacing revenue CAGR (operating leverage)",
         "Revenue growing slower than profits shows improving operating leverage and scale benefits",
         p11_operating_leverage),
    Rule("PRO_12", "pro", "Balance sheet assets growing with declining debt",
         "Growing asset base funded by internal accruals reflects self-sustaining growth",
         p12_assets_up_debt_down, non_financial_only=True),
    Rule("CON_01", "con", "D/E > 2.0 for non-financial companies",
         "Debt-to-equity ratio of {x:.2f} is elevated for a non-financial company and warrants monitoring",
         c1_high_de, non_financial_only=True),
    Rule("CON_02", "con", "FCF negative for 3 consecutive years",
         "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
         c2_fcf_negative),
    Rule("CON_03", "con", "OPM declining for 3 consecutive years",
         "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
         c3_opm_declining, non_financial_only=True),
    Rule("CON_04", "con", "Net profit negative in latest year",
         "Company reported a net loss in the most recent financial year",
         c4_net_loss),
    Rule("CON_05", "con", "Revenue declining for 2+ years",
         "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
         c5_revenue_decline),
    Rule("CON_06", "con", "ICR < 1.5",
         "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
         c6_low_icr, non_financial_only=True),
    Rule("CON_07", "con", "Dividend payout > 100%",
         "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
         c7_payout_over_100),
    Rule("CON_08", "con", "D/E rising for 3 consecutive years",
         "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
         c8_de_rising, non_financial_only=True),
    Rule("CON_09", "con", "EPS declining for 3 consecutive years",
         "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
         c9_eps_declining),
    Rule("CON_10", "con", "ROCE < 10%",
         "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
         c10_low_roce, non_financial_only=True),
    Rule("CON_11", "con", "Net Debt > 3x EBITDA",
         "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
         c11_net_debt_ebitda, non_financial_only=True),
    Rule("CON_12", "con", "Revenue CAGR < 5% over 5 years",
         "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
         c12_low_revenue_cagr),
]


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def confidence_pct(signal: Signal) -> float:
    return round((60.0 + 40.0 * clip01(signal.strength)) * clip01(signal.coverage), 1)


def evaluate_company(ctx: CompanyContext, threshold: float = settings.CONFIDENCE_THRESHOLD) -> List[Dict]:
    """Run all rules for one company; keep signals with confidence > threshold."""
    rows: List[Dict] = []
    for rule in RULES:
        if rule.non_financial_only and ctx.is_financial:
            continue
        try:
            signal = rule.evaluate(ctx)
        except Exception as exc:  # a bad data point must never stop the batch
            log.warning("Rule %s failed for %s: %s", rule.rule_id, ctx.ticker, exc)
            continue
        if signal is None:
            continue
        conf = confidence_pct(signal)
        if conf > threshold:
            rows.append({"company_id": ctx.company_id, "type": rule.kind, "rule_id": rule.rule_id,
                         "text": rule.text.format(**signal.fmt) if signal.fmt else rule.text,
                         "confidence_pct": conf})
    return rows


_FALLBACK_METRICS = (
    ("roe", "Return on equity", False),
    ("opm", "Operating margin", True),
    ("roce", "Return on capital employed", True),
    ("sales_cagr_5", "5-year revenue CAGR", False),
    ("pat_cagr_5", "5-year net profit CAGR", False),
)


def _sector_medians(store: DataStore) -> Dict[str, Dict[str, float]]:
    rows = []
    for _, comp in store.companies.iterrows():
        k = company_kpis(store.frame_for(comp["company_id"]))
        k["sector"], k["company_id"], k["is_financial"] = comp["sector"], comp["company_id"], comp["is_financial"]
        rows.append(k)
    df = pd.DataFrame(rows)
    return {m: df.groupby("sector")[m].median().to_dict() for m, _, _ in _FALLBACK_METRICS}


def _fallback_statement(ctx: CompanyContext, kind: str, medians) -> Optional[Dict]:
    kpis = company_kpis(ctx.frame.reset_index() if len(ctx.frame) else ctx.frame)
    best = None
    for key, label, non_fin_only in _FALLBACK_METRICS:
        if non_fin_only and ctx.is_financial:
            continue
        value, med = kpis.get(key, NAN), medians[key].get(ctx.sector, NAN)
        if is_nan(value) or is_nan(med):
            continue
        diff = value - med
        better = diff if kind == "pro" else -diff
        if best is None or better > best[0]:
            best = (better, label, value, med, diff)
    if best is None:
        return None
    _, label, value, med, diff = best
    if diff >= 0:
        text = f"{label} of {value:.1f}% is above the sector median of {med:.1f}%" if kind == "pro" else \
               f"{label} of {value:.1f}% is the closest metric to the sector median of {med:.1f}%, with no standout weakness"
    else:
        text = f"{label} of {value:.1f}% is below the sector median of {med:.1f}%" if kind == "con" else \
               f"{label} of {value:.1f}% is the closest metric to the sector median of {med:.1f}%, with no standout strength"
    return {"company_id": ctx.company_id, "type": kind, "rule_id": "PRO_FB" if kind == "pro" else "CON_FB",
            "text": text, "confidence_pct": settings.FALLBACK_CONFIDENCE}


def generate_pros_cons(store: DataStore, threshold: float = settings.CONFIDENCE_THRESHOLD) -> pd.DataFrame:
    medians = _sector_medians(store)
    rows: List[Dict] = []
    fallbacks = 0
    for _, comp in store.companies.iterrows():
        ctx = CompanyContext(comp, store.frame_for(comp["company_id"]))
        found = evaluate_company(ctx, threshold)
        for kind in ("pro", "con"):
            if not any(r["type"] == kind for r in found):
                fb = _fallback_statement(ctx, kind, medians)
                if fb:
                    found.append(fb)
                    fallbacks += 1
        rows.extend(found)
    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    df["_order"] = df["type"].map({"pro": 0, "con": 1})
    df = (df.sort_values(["company_id", "_order", "confidence_pct"], ascending=[True, True, False])
            .drop(columns="_order").reset_index(drop=True))
    log.info("Generated %d statements (%d sector-relative fallbacks)", len(df), fallbacks)
    return df


def verify_coverage(df: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    """Return companies missing a pro and/or a con (empty frame == PASS)."""
    have_pro = set(df.loc[df["type"] == "pro", "company_id"])
    have_con = set(df.loc[df["type"] == "con", "company_id"])
    gaps = []
    for _, c in companies.iterrows():
        cid = c["company_id"]
        if cid not in have_pro or cid not in have_con:
            gaps.append({"company_id": cid, "ticker": c["ticker"],
                         "missing_pro": cid not in have_pro, "missing_con": cid not in have_con})
    return pd.DataFrame(gaps, columns=["company_id", "ticker", "missing_pro", "missing_con"])


def run(store: DataStore) -> pd.DataFrame:
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_pros_cons(store)
    df.to_csv(settings.PROS_CONS_CSV, index=False)
    gaps = verify_coverage(df, store.companies)
    if len(gaps):
        log.error("Coverage FAILED for %d companies: %s", len(gaps), gaps["ticker"].tolist())
    else:
        log.info("Coverage PASSED: every company has >= 1 pro and >= 1 con")
    return df
