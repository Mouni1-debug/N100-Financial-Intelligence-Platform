"""Central configuration for Sprint 5 - Intelligence, NLP & PDF Reports.

Every path, threshold and label used by the sprint lives here so that nothing
is hard-coded inside the business-logic modules.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Directories
# --------------------------------------------------------------------------- #
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"

REPORTS_DIR = ROOT_DIR / "reports"
TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
TEARSHEET_TEST_DIR = REPORTS_DIR / "tearsheets_test"
SECTOR_DIR = REPORTS_DIR / "sector"
PORTFOLIO_DIR = REPORTS_DIR / "portfolio"

# --------------------------------------------------------------------------- #
# Input files (produced by Sprints 1-4)
# --------------------------------------------------------------------------- #
ANALYSIS_XLSX = RAW_DIR / "analysis.xlsx"

INPUT_FILES = {
    "companies": PROCESSED_DIR / "companies.csv",
    "profit_loss": PROCESSED_DIR / "profit_loss.csv",
    "balance_sheet": PROCESSED_DIR / "balance_sheet.csv",
    "cash_flow": PROCESSED_DIR / "cash_flow.csv",
    "ratios": PROCESSED_DIR / "ratios.csv",                       # Ratio Engine (Sprint 3/4)
    "ratio_engine_cagr": PROCESSED_DIR / "ratio_engine_cagr.csv",  # computed CAGR (Ratio Engine)
    "capital_allocation": PROCESSED_DIR / "capital_allocation.csv",  # Sprint 2
    "analysis": ANALYSIS_XLSX,
}

# --------------------------------------------------------------------------- #
# Output files (Sprint 5 deliverables)
# --------------------------------------------------------------------------- #
ANALYSIS_PARSED_CSV = OUTPUT_DIR / "analysis_parsed.csv"
PARSE_FAILURES_CSV = OUTPUT_DIR / "parse_failures.csv"
CAGR_VALIDATION_CSV = OUTPUT_DIR / "cagr_cross_validation.csv"
PROS_CONS_CSV = OUTPUT_DIR / "pros_cons_generated.csv"
CASHFLOW_XLSX = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_ALERTS_CSV = OUTPUT_DIR / "distress_alerts.csv"
CAPITAL_ALLOCATION_GAPS_CSV = OUTPUT_DIR / "capital_allocation_gaps.csv"
PATTERN_DISTRIBUTION_CSV = OUTPUT_DIR / "pattern_distribution.csv"
PATTERN_CHANGES_CSV = OUTPUT_DIR / "pattern_changes.csv"
SKIPPED_TEARSHEETS_CSV = OUTPUT_DIR / "skipped_tearsheets.csv"
PORTFOLIO_PDF = PORTFOLIO_DIR / "portfolio_summary.pdf"

# --------------------------------------------------------------------------- #
# Day 29 - NLP parser
# --------------------------------------------------------------------------- #
TARGET_TEXT_FIELDS = (
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
)
CAGR_DIVERGENCE_PP = 5.0  # percentage points; larger gaps are flagged for manual review

# --------------------------------------------------------------------------- #
# Day 30 - Pros / cons generator
# --------------------------------------------------------------------------- #
CONFIDENCE_THRESHOLD = 60.0   # only keep signals with confidence strictly above this
FALLBACK_CONFIDENCE = 61.0    # confidence given to sector-relative fallback statements

# --------------------------------------------------------------------------- #
# Day 31 - Cash flow intelligence
# --------------------------------------------------------------------------- #
CFO_QUALITY_WINDOW_YEARS = 5
CFO_QUALITY_HIGH = 1.0        # > 1.0  -> High Quality
CFO_QUALITY_MODERATE = 0.5    # 0.5-1.0 -> Moderate, < 0.5 -> Accrual Risk
CAPEX_ASSET_LIGHT = 3.0       # < 3%   -> Asset Light
CAPEX_CAPITAL_INTENSIVE = 8.0  # > 8%   -> Capital Intensive, 3-8% -> Moderate

# --------------------------------------------------------------------------- #
# Day 32 - Capital allocation
# --------------------------------------------------------------------------- #
# The eight patterns produced in Sprint 2. Align these names with your
# capital_allocation.csv; unknown names are still counted and reported.
CAPITAL_ALLOCATION_PATTERNS = (
    "Reinvestor",
    "Aggressive Expander",
    "Asset Monetizer",
    "Cash Accumulator",
    "Capital Raiser",
    "Cash Burner",
    "Distress Signal",
    "Asset Liquidator",
)

# --------------------------------------------------------------------------- #
# Day 33-35 - Reports
# --------------------------------------------------------------------------- #
TEST_TICKERS = ("TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL")
MIN_YEARS_FOR_TEARSHEET = 3
MIN_TEARSHEET_SIZE_KB = 30
EXPECTED_COMPANIES = 92
EXPECTED_SECTORS = 11
FLAT_TOLERANCE_PCT = 2.0      # +/- band treated as "flat" for portfolio trend arrows
PLATFORM_NAME = "N100 Financial Intelligence Platform"


def ensure_directories() -> None:
    """Create every output directory if it does not exist yet."""
    for path in (
        RAW_DIR, PROCESSED_DIR, OUTPUT_DIR, LOG_DIR,
        TEARSHEET_DIR, TEARSHEET_TEST_DIR, SECTOR_DIR, PORTFOLIO_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
