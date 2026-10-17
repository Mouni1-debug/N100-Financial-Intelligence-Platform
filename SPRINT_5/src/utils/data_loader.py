"""Validated access to every input table used in Sprint 5.

``DataStore`` reads the CSV/XLSX files produced by earlier sprints, checks that
the required columns exist and exposes a merged ``fundamentals`` table
(profit & loss + balance sheet + cash flow + ratios) keyed by company and year.

For unit tests a ``DataStore`` can also be built from in-memory DataFrames.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class DataValidationError(Exception):
    """Raised when an input file is missing or lacks required columns."""


REQUIRED_COLUMNS: Dict[str, list] = {
    "companies": ["company_id", "company_name", "ticker", "sector", "is_financial"],
    "profit_loss": ["company_id", "year", "sales", "operating_profit", "opm_pct",
                    "net_profit", "eps", "dividend_payout_pct", "interest"],
    "balance_sheet": ["company_id", "year", "equity_capital", "reserves",
                      "borrowings", "other_liabilities", "total_assets"],
    "cash_flow": ["company_id", "year", "operating_activity", "investing_activity",
                  "financing_activity", "net_cash_flow"],
    "ratios": ["company_id", "year", "roe_pct", "roce_pct", "de_ratio", "icr",
               "dividend_yield_pct", "fcf", "ebitda", "net_debt"],
    "ratio_engine_cagr": ["company_id", "metric_type", "period_years", "value_pct"],
    "capital_allocation": ["company_id", "year", "pattern"],
    "analysis": ["company_id", *settings.TARGET_TEXT_FIELDS],
}

_TEXT_COLUMNS = {"company_name", "ticker", "sector", "pattern", "metric_type",
                 *settings.TARGET_TEXT_FIELDS}
_TRUE = {"true", "1", "yes", "y", "t"}


def _read_any(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise DataValidationError(f"Input file not found: {path}")
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


class DataStore:
    """Lazy, cached access to all Sprint 5 inputs."""

    def __init__(self, frames: Optional[Dict[str, pd.DataFrame]] = None) -> None:
        self._frames = dict(frames or {})
        self._cache: Dict[str, pd.DataFrame] = {}
        self._by_company: Optional[dict] = None

    # ------------------------------------------------------------------ #
    def table(self, name: str) -> pd.DataFrame:
        if name in self._cache:
            return self._cache[name]
        df = self._frames[name].copy() if name in self._frames else _read_any(settings.INPUT_FILES[name])
        df = self._validate_and_normalise(name, df)
        self._cache[name] = df
        return df

    def _validate_and_normalise(self, name: str, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        missing = [c for c in REQUIRED_COLUMNS[name] if c not in df.columns]
        if missing:
            raise DataValidationError(f"Table '{name}' is missing required columns: {missing}")
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            df = df.dropna(subset=["year"])
            df["year"] = df["year"].astype(int)
            dupes = df.duplicated(["company_id", "year"], keep="last")
            if dupes.any():
                log.warning("Table '%s': dropped %d duplicate company/year rows", name, int(dupes.sum()))
                df = df[~dupes]
        if name == "companies":
            df["is_financial"] = df["is_financial"].map(
                lambda v: str(v).strip().lower() in _TRUE)
        elif name != "analysis":
            for col in df.columns:
                if col not in _TEXT_COLUMNS and col not in {"company_id", "year"}:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------ #
    @property
    def companies(self) -> pd.DataFrame:
        return self.table("companies").sort_values("company_id").reset_index(drop=True)

    @property
    def fundamentals(self) -> pd.DataFrame:
        """Profit & loss + balance sheet + cash flow + ratios on (company_id, year)."""
        if "fundamentals" in self._cache:
            return self._cache["fundamentals"]
        merged = None
        for name in ("profit_loss", "balance_sheet", "cash_flow", "ratios"):
            part = self.table(name)
            merged = part if merged is None else merged.merge(
                part, on=["company_id", "year"], how="outer", suffixes=("", f"_{name}"))
        merged = merged.sort_values(["company_id", "year"]).reset_index(drop=True)
        self._cache["fundamentals"] = merged
        return merged

    @property
    def latest_year(self) -> int:
        return int(self.fundamentals["year"].max())

    def frame_for(self, company_id) -> pd.DataFrame:
        """Fundamentals of one company, sorted by year (empty frame if none)."""
        if self._by_company is None:
            self._by_company = {cid: grp.reset_index(drop=True)
                                for cid, grp in self.fundamentals.groupby("company_id")}
        return self._by_company.get(company_id, self.fundamentals.iloc[0:0])

    def years_available(self, company_id) -> int:
        frame = self.frame_for(company_id)
        if frame.empty:
            return 0
        return int(frame["sales"].notna().sum())
