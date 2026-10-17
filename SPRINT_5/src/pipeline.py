"""Day-by-day orchestration for Sprint 5. Each ``run_dayNN`` is independent and
re-runnable; steps that need earlier outputs rebuild them automatically."""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from config import settings
from src.analytics import capital_allocation, cashflow_kpis
from src.nlp import parser, pros_cons_generator
from src.reports import portfolio_summary, sector_report, tearsheet
from src.utils.data_loader import DataStore
from src.utils.logger import get_logger
from src.utils.pdf_utils import blank_pages, count_pages

log = get_logger(__name__)


def _pros_cons(store: DataStore) -> pd.DataFrame:
    if settings.PROS_CONS_CSV.exists():
        return pd.read_csv(settings.PROS_CONS_CSV)
    return pros_cons_generator.run(store)


def _allocation(store: DataStore) -> Dict:
    try:
        return capital_allocation.latest_labels(store.table("capital_allocation"))
    except Exception as exc:
        log.warning("Capital allocation labels unavailable: %s", exc)
        return {}


def run_day29(store: DataStore):
    return parser.run(store)


def run_day30(store: DataStore):
    return pros_cons_generator.run(store)


def run_day31(store: DataStore):
    return cashflow_kpis.run(store)


def run_day32(store: DataStore):
    result = capital_allocation.run(store)
    cashflow_kpis.run(store)   # refresh workbook so the allocation column is up to date
    return result


def run_day33(store: DataStore, tickers: Optional[List[str]] = None):
    """Build test tearsheets (5 sectors) and assert each has exactly 2 pages."""
    wanted = list(tickers or settings.TEST_TICKERS)
    present = set(store.companies["ticker"])
    chosen = [t for t in wanted if t in present]
    if len(chosen) < len(wanted):
        log.warning("Test tickers not found in data: %s", sorted(set(wanted) - present))
    results, _ = tearsheet.batch_generate(store, _pros_cons(store), _allocation(store),
                                          out_dir=settings.TEARSHEET_TEST_DIR, tickers=chosen, skipped_csv=None)
    for r in results:
        pages, blanks = count_pages(r["path"]), blank_pages(r["path"])
        status = "OK" if pages == 2 and not blanks and r["shrink"] >= tearsheet.SHRINK_WARN else "CHECK"
        log.info("[%s] %s | pages=%d | blank=%s | fit=%.0f%%", status, r["ticker"], pages, blanks, r["shrink"] * 100)
    return results


def run_day34(store: DataStore):
    results, skipped = tearsheet.batch_generate(store, _pros_cons(store), _allocation(store))
    sectors = sector_report.batch_generate_sector_reports(store)
    return {"tearsheets": results, "skipped": skipped, "sector_reports": sectors}


def run_day35(store: DataStore):
    return portfolio_summary.generate_portfolio_summary(store)


STEPS = {29: run_day29, 30: run_day30, 31: run_day31, 32: run_day32,
         33: run_day33, 34: run_day34, 35: run_day35}


def run_all(store: DataStore) -> None:
    for day in sorted(STEPS):
        log.info("=== Day %d ===", day)
        STEPS[day](store)
