"""Day 32 - Capital allocation completeness check, distribution and pattern changes."""
from __future__ import annotations

from typing import Dict

import pandas as pd

from config import settings
from src.utils.data_loader import DataStore
from src.utils.logger import get_logger

log = get_logger(__name__)


def validate_completeness(ca: pd.DataFrame, expected: pd.DataFrame) -> pd.DataFrame:
    """Return every (company_id, year) present in the fundamentals but missing a pattern."""
    have = ca.dropna(subset=["pattern"])[["company_id", "year"]].drop_duplicates()
    have = have.assign(_present=True)
    merged = expected[["company_id", "year"]].drop_duplicates().merge(
        have, on=["company_id", "year"], how="left")
    return merged[merged["_present"].isna()][["company_id", "year"]].reset_index(drop=True)


def latest_labels(ca: pd.DataFrame) -> Dict:
    """Mapping company_id -> pattern in that company's latest classified year."""
    latest = ca.dropna(subset=["pattern"]).sort_values("year").groupby("company_id").tail(1)
    return dict(zip(latest["company_id"], latest["pattern"]))


def distribution(ca: pd.DataFrame, year: int) -> pd.DataFrame:
    """Count of companies per pattern in ``year`` (all 8 configured patterns always listed)."""
    counts = ca[ca["year"] == year]["pattern"].value_counts()
    patterns = list(settings.CAPITAL_ALLOCATION_PATTERNS) + [
        p for p in counts.index if p not in settings.CAPITAL_ALLOCATION_PATTERNS]
    out = pd.DataFrame({"pattern": patterns})
    out["companies"] = out["pattern"].map(counts).fillna(0).astype(int)
    total = max(int(out["companies"].sum()), 1)
    out["share_pct"] = (out["companies"] / total * 100).round(1)
    out["configured_pattern"] = out["pattern"].isin(settings.CAPITAL_ALLOCATION_PATTERNS)
    return out


def pattern_changes(ca: pd.DataFrame, companies: pd.DataFrame) -> pd.DataFrame:
    """Year-over-year pattern transitions, e.g. Reinvestor -> Distress Signal."""
    df = ca.dropna(subset=["pattern"]).sort_values(["company_id", "year"]).copy()
    df["from_pattern"] = df.groupby("company_id")["pattern"].shift()
    df["from_year"] = df.groupby("company_id")["year"].shift()
    changed = df[df["from_pattern"].notna() & (df["from_pattern"] != df["pattern"])]
    out = changed.rename(columns={"year": "to_year", "pattern": "to_pattern"})
    out = out.merge(companies[["company_id", "ticker", "company_name", "sector"]], on="company_id", how="left")
    out["from_year"] = out["from_year"].astype(int)
    out["moved_to_distress"] = out["to_pattern"].eq("Distress Signal")
    cols = ["company_id", "ticker", "company_name", "sector", "from_year", "to_year",
            "from_pattern", "to_pattern", "moved_to_distress"]
    return out[cols].sort_values(["to_year", "ticker"], ascending=[False, True]).reset_index(drop=True)


def run(store: DataStore) -> Dict[str, object]:
    ca = store.table("capital_allocation")
    gaps = validate_completeness(ca, store.fundamentals)
    gaps.to_csv(settings.CAPITAL_ALLOCATION_GAPS_CSV, index=False)
    if len(gaps):
        log.warning("capital_allocation.csv is missing %d company-year rows (see %s)",
                    len(gaps), settings.CAPITAL_ALLOCATION_GAPS_CSV.name)
    else:
        log.info("capital_allocation.csv is complete for all companies x all years")

    dist = distribution(ca, store.latest_year)
    dist.to_csv(settings.PATTERN_DISTRIBUTION_CSV, index=False)
    changes = pattern_changes(ca, store.companies)
    changes.to_csv(settings.PATTERN_CHANGES_CSV, index=False)
    log.info("Pattern distribution (%d): %s", store.latest_year,
             dict(zip(dist["pattern"], dist["companies"])))
    log.info("%d year-over-year pattern changes saved", len(changes))
    return {"gaps": len(gaps), "distribution": dist, "changes": len(changes)}
