"""Day 29 - NLP analysis text parser.

Parses free-text growth statements in ``analysis.xlsx`` such as::

    10 Years: 21%
    5 Years: 18.5%

into a tidy table ``company_id, metric_type, period_years, value_pct``.
Entries that do not match are written to ``output/parse_failures.csv`` and the
parsed values are cross-validated against the Ratio Engine's computed CAGRs.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

import pandas as pd

from config import settings
from src.utils.data_loader import DataStore
from src.utils.helpers import is_nan
from src.utils.logger import get_logger

log = get_logger(__name__)

# Sprint spec pattern: (\d+)\s*Years?:?\s*([\d.]+)%
# Extended with an optional minus sign so negative growth ("5 Years: -3%") is kept.
PERIOD_VALUE_PATTERN = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%", re.IGNORECASE)

PARSED_COLUMNS = ["company_id", "metric_type", "period_years", "value_pct"]
FAILURE_COLUMNS = ["company_id", "metric_type", "unmatched_text"]


def parse_text_cell(text) -> Tuple[List[Tuple[int, float]], List[str]]:
    """Parse one cell. Returns ``(matches, failures)``.

    ``matches``  - list of ``(period_years, value_pct)``
    ``failures`` - text fragments that could not be parsed
    """
    if is_nan(text) or not str(text).strip():
        return [], ["<empty>"]

    raw = str(text)
    matches: List[Tuple[int, float]] = []
    failures: List[str] = []

    for m in PERIOD_VALUE_PATTERN.finditer(raw):
        try:
            matches.append((int(m.group(1)), float(m.group(2))))
        except ValueError:
            failures.append(m.group(0).strip())

    if not matches and not failures:
        failures.append(" ".join(raw.split()))
    elif matches:
        # Look for leftover numeric fragments the pattern did not understand (e.g. "TTM: 12%")
        leftover = PERIOD_VALUE_PATTERN.sub(" ", raw)
        for seg in re.split(r"[\n;|]+", leftover):
            seg = seg.strip(" :;,|-\u2022\t\r")
            if seg and re.search(r"[\d%]", seg):
                failures.append(" ".join(seg.split()))
    return matches, failures


def parse_analysis(analysis: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Parse all target fields. Returns ``(parsed_df, failures_df)``."""
    parsed: List[Dict] = []
    failed: List[Dict] = []
    for _, row in analysis.iterrows():
        for field in settings.TARGET_TEXT_FIELDS:
            matches, failures = parse_text_cell(row.get(field))
            for period, value in matches:
                parsed.append({"company_id": row["company_id"], "metric_type": field,
                               "period_years": period, "value_pct": value})
            for frag in failures:
                failed.append({"company_id": row["company_id"], "metric_type": field,
                               "unmatched_text": frag})
    parsed_df = pd.DataFrame(parsed, columns=PARSED_COLUMNS)
    failures_df = pd.DataFrame(failed, columns=FAILURE_COLUMNS)
    if not parsed_df.empty:
        parsed_df = parsed_df.drop_duplicates(["company_id", "metric_type", "period_years"])
        parsed_df = parsed_df.sort_values(["company_id", "metric_type", "period_years"],
                                          ascending=[True, True, False]).reset_index(drop=True)
    return parsed_df, failures_df


def cross_validate_cagr(parsed: pd.DataFrame, engine_cagr: pd.DataFrame,
                        tolerance_pp: float = settings.CAGR_DIVERGENCE_PP) -> pd.DataFrame:
    """Compare parsed values with the Ratio Engine; flag |difference| > tolerance (pp)."""
    keys = ["company_id", "metric_type", "period_years"]
    engine = engine_cagr[keys + ["value_pct"]].rename(columns={"value_pct": "engine_value_pct"})
    merged = parsed.rename(columns={"value_pct": "parsed_value_pct"}).merge(engine, on=keys, how="inner")
    merged["difference_pp"] = (merged["parsed_value_pct"] - merged["engine_value_pct"]).round(2)
    merged["needs_review"] = merged["difference_pp"].abs() > tolerance_pp
    return merged.sort_values(["needs_review", "difference_pp"], ascending=[False, False]).reset_index(drop=True)


def run(store: DataStore) -> Dict[str, int]:
    """Execute the full Day 29 task and write all three output files."""
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parsed, failures = parse_analysis(store.table("analysis"))
    parsed.to_csv(settings.ANALYSIS_PARSED_CSV, index=False)
    failures.to_csv(settings.PARSE_FAILURES_CSV, index=False)

    validation = cross_validate_cagr(parsed, store.table("ratio_engine_cagr"))
    validation.to_csv(settings.CAGR_VALIDATION_CSV, index=False)

    flagged = int(validation["needs_review"].sum()) if not validation.empty else 0
    log.info("Parsed %d values | %d parse failures | %d/%d CAGR values flagged (> %.0f pp)",
             len(parsed), len(failures), flagged, len(validation), settings.CAGR_DIVERGENCE_PP)
    return {"parsed": len(parsed), "failures": len(failures),
            "compared": len(validation), "flagged": flagged}
