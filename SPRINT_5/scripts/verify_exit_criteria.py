"""Check every Sprint 5 exit criterion and print a PASS / FAIL report.

    python scripts/verify_exit_criteria.py
Exit status 0 = all automated criteria passed.
(The 5-tearsheet visual review and the lead sign-off remain manual.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from config import settings  # noqa: E402
from src.analytics.cashflow_kpis import SPEC_COLUMNS  # noqa: E402
from src.nlp.pros_cons_generator import verify_coverage  # noqa: E402
from src.utils.data_loader import DataStore  # noqa: E402
from src.utils.pdf_utils import blank_pages, count_pages  # noqa: E402


def main() -> int:
    store = DataStore()
    companies = store.companies
    results = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ->  {detail}" if detail else ""))

    # 1. pros / cons coverage
    if settings.PROS_CONS_CSV.exists():
        pc = pd.read_csv(settings.PROS_CONS_CSV)
        gaps = verify_coverage(pc, companies)
        check("pros_cons_generated.csv: >=1 pro and >=1 con per company", gaps.empty,
              f"{len(companies) - len(gaps)}/{len(companies)} companies covered")
        check("pros_cons_generated.csv: confidence > 60 and exact columns",
              bool((pc["confidence_pct"] > settings.CONFIDENCE_THRESHOLD).all())
              and list(pc.columns) == ["company_id", "type", "rule_id", "text", "confidence_pct"])
    else:
        check("pros_cons_generated.csv exists", False)

    # 2. analysis_parsed.csv
    check("analysis_parsed.csv exists", settings.ANALYSIS_PARSED_CSV.exists())

    # 3. cashflow workbook
    if settings.CASHFLOW_XLSX.exists():
        cf = pd.read_excel(settings.CASHFLOW_XLSX, sheet_name="Cash Flow Intelligence")
        check("cashflow_intelligence.xlsx: one row per company", len(cf) == len(companies),
              f"{len(cf)} rows / {len(companies)} companies")
        check("cashflow_intelligence.xlsx: all required columns", list(cf.columns) == SPEC_COLUMNS)
    else:
        check("cashflow_intelligence.xlsx exists", False)
    check("distress_alerts.csv exists", settings.DISTRESS_ALERTS_CSV.exists())

    # 4. tearsheets
    skipped = pd.read_csv(settings.SKIPPED_TEARSHEETS_CSV) if settings.SKIPPED_TEARSHEETS_CSV.exists() else pd.DataFrame()
    expected = len(companies) - len(skipped)
    pdfs = sorted(settings.TEARSHEET_DIR.glob("*_tearsheet.pdf"))
    check("tearsheets: count == companies - skipped", len(pdfs) == expected,
          f"{len(pdfs)} files, expected {expected} ({len(skipped)} skipped)")
    small = [p.name for p in pdfs if p.stat().st_size < settings.MIN_TEARSHEET_SIZE_KB * 1024]
    check(f"tearsheets: every file >= {settings.MIN_TEARSHEET_SIZE_KB} KB", not small, f"too small: {small[:5]}")
    bad_pages = [p.name for p in pdfs if count_pages(p) != 2]
    check("tearsheets: exactly 2 pages each", not bad_pages, f"wrong page count: {bad_pages[:5]}")
    blanks = [p.name for p in pdfs if blank_pages(p)]
    check("tearsheets: no blank pages", not blanks, f"blank pages in: {blanks[:5]}")

    # 5. sector + portfolio
    n_sectors = companies["sector"].nunique()
    sector_pdfs = list(settings.SECTOR_DIR.glob("*_report.pdf"))
    check("sector reports: one PDF per sector", len(sector_pdfs) == n_sectors, f"{len(sector_pdfs)}/{n_sectors}")
    if settings.PORTFOLIO_PDF.exists():
        check("portfolio_summary.pdf: one page per company", count_pages(settings.PORTFOLIO_PDF) == len(companies),
              f"{count_pages(settings.PORTFOLIO_PDF)} pages")
    else:
        check("portfolio_summary.pdf exists", False)

    print("\nManual items still open: visual review of 5 tearsheets, Sprint 5 review & team-lead sign-off.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
