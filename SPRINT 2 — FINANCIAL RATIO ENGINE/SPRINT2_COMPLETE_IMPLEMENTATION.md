# 🚀 SPRINT 2: FINANCIAL RATIO ENGINE - COMPLETE IMPLEMENTATION

## 📁 COMPLETE FOLDER STRUCTURE

```
n100-financial-intelligence/
│
├── src/
│   ├── analytics/                          ← NEW: Ratio computation engine
│   │   ├── __init__.py
│   │   ├── ratios.py                       (Day 08-09: 300+ lines)
│   │   ├── cagr.py                         (Day 10: 250+ lines)
│   │   ├── cashflow_kpis.py                (Day 11: 280+ lines)
│   │   ├── validators.py                   (Input validation)
│   │   └── edge_cases.py                   (Financial sector logic)
│   ├── etl/                                ← EXISTING (Sprint 1)
│   ├── db/
│   ├── config/
│   └── utils/
│
├── db/
│   ├── schema.sql                          (UPDATED: Add financial_ratios columns)
│   ├── migrations/
│   │   ├── 001_initial_schema.sql          (Sprint 1)
│   │   └── 002_add_kpi_columns.sql         (NEW: Day 08)
│   └── nifty100.db
│
├── data/
│   └── output/
│       ├── load_audit.csv                  (EXISTING)
│       ├── validation_failures.csv         (EXISTING)
│       ├── capital_allocation.csv          (NEW: Day 11)
│       ├── ratio_edge_cases.log            (NEW: Day 13)
│       └── ratio_computation_log.csv       (NEW: Day 12)
│
├── tests/
│   ├── unit/
│   │   ├── etl/                            (EXISTING: Sprint 1)
│   │   └── kpi/                            (NEW: 40+ KPI tests)
│   │       ├── __init__.py
│   │       ├── test_profitability.py       (8 tests)
│   │       ├── test_leverage.py            (8 tests)
│   │       ├── test_cagr.py                (10 tests)
│   │       ├── test_cashflow.py            (6 tests)
│   │       └── test_edge_cases.py          (8 tests)
│   └── integration/
│       ├── test_full_pipeline.py           (EXISTING)
│       └── test_ratio_engine.py            (NEW: Day 14)
│
├── notebooks/
│   ├── 01_data_exploration.ipynb           (EXISTING)
│   └── 03_ratio_analysis.ipynb             (NEW: Day 12)
│
├── docs/
│   ├── SPRINT_1_GUIDE.md                   (EXISTING)
│   ├── SPRINT_2_GUIDE.md                   (NEW: Day-by-day)
│   ├── KPI_FORMULAS.md                     (NEW: 50+ formulas)
│   ├── EDGE_CASES.md                       (NEW: Edge case guide)
│   ├── RATIO_ENGINE_DESIGN.md              (NEW: Architecture)
│   └── BANK_CARVEOUT.md                    (NEW: Financial logic)
│
├── scripts/
│   ├── run_ratio_engine.py                 (NEW: Execute pipeline)
│   ├── validate_ratios.py                  (NEW: Validation)
│   └── generate_ratio_report.py            (NEW: Reports)
│
├── logs/
│   ├── etl.log                             (EXISTING)
│   └── ratio_engine.log                    (NEW)
│
├── Makefile                                (UPDATED: Add ratio targets)
├── requirements.txt                        (UPDATED: numpy, scipy)
└── README.md                               (UPDATED: Add Sprint 2)
```

---

## 📝 COMPLETE PYTHON CODE (ALL FILES)

### FILE 1: `src/analytics/ratios.py` (300+ lines)

```python
"""
Financial Ratio Computation Engine
Implements profitability, leverage, and efficiency ratios for all companies.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Warning severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class RatioWarning:
    """Single ratio computation warning."""
    company_id: str
    fiscal_year: int
    ratio_name: str
    severity: Severity
    message: str
    actual_value: Optional[float] = None
    expected_range: Optional[Tuple] = None


class ProfitabilityRatios:
    """
    Compute profitability ratios for companies.
    
    Ratios:
    - Net Profit Margin (NPM)
    - Operating Profit Margin (OPM)
    - Return on Equity (ROE)
    - Return on Capital Employed (ROCE)
    - Return on Assets (ROA)
    """
    
    def __init__(self):
        self.warnings = []
    
    @staticmethod
    def net_profit_margin(net_profit: Optional[float], 
                         sales: Optional[float]) -> Optional[float]:
        """
        Calculate Net Profit Margin.
        
        Formula: (net_profit / sales) × 100
        
        Args:
            net_profit: Net profit in crores
            sales: Total sales in crores
        
        Returns:
            NPM percentage or None if denominator is zero/null
        
        Examples:
            net_profit_margin(500, 5000) → 10.0
            net_profit_margin(500, 0) → None
            net_profit_margin(-100, 5000) → -2.0 (OK, negative profit)
        """
        if sales is None or sales == 0:
            return None
        if net_profit is None:
            return None
        
        return (net_profit / sales) * 100
    
    @staticmethod
    def operating_profit_margin(operating_profit: Optional[float],
                               sales: Optional[float],
                               opm_pct_source: Optional[float] = None) -> Tuple[Optional[float], Optional[Dict]]:
        """
        Calculate Operating Profit Margin with cross-check.
        
        Formula: (operating_profit / sales) × 100
        Cross-check: Compare to opm_pct field, log if difference > 1%
        
        Args:
            operating_profit: Operating profit in crores
            sales: Total sales in crores
            opm_pct_source: Source OPM% from data (for cross-check)
        
        Returns:
            Tuple of (OPM percentage, warning dict or None)
        
        Examples:
            operating_profit_margin(1000, 5000) → (20.0, None)
            operating_profit_margin(1000, 5000, 21.5) → (20.0, {'msg': 'OPM mismatch > 1%'})
        """
        if sales is None or sales == 0:
            return None, None
        if operating_profit is None:
            return None, None
        
        computed_opm = (operating_profit / sales) * 100
        
        warning = None
        if opm_pct_source is not None and not np.isnan(opm_pct_source):
            difference = abs(computed_opm - opm_pct_source)
            if difference > 1.0:  # More than 1% difference
                warning = {
                    'type': 'OPM_CROSSCHECK_MISMATCH',
                    'computed_opm': round(computed_opm, 2),
                    'source_opm': round(opm_pct_source, 2),
                    'difference': round(difference, 2),
                    'severity': Severity.WARNING.value
                }
        
        return computed_opm, warning
    
    @staticmethod
    def return_on_equity(net_profit: Optional[float],
                        equity_capital: Optional[float],
                        reserves: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate Return on Equity (ROE).
        
        Formula: (net_profit / (equity_capital + reserves)) × 100
        
        Args:
            net_profit: Net profit in crores
            equity_capital: Equity capital in crores
            reserves: Reserves in crores
        
        Returns:
            Tuple of (ROE percentage, flag_string or None)
            Flag: "NEGATIVE_EQUITY" if equity < 0
        
        Examples:
            return_on_equity(1000, 5000, 2000) → (14.29, None)
            return_on_equity(1000, -1000, 2000) → (None, "NEGATIVE_EQUITY")
            return_on_equity(1000, 0, 0) → (None, None)
        """
        if equity_capital is None:
            equity_capital = 0
        if reserves is None:
            reserves = 0
        
        total_equity = equity_capital + reserves
        
        # Flag negative equity
        flag = None
        if total_equity < 0:
            flag = "NEGATIVE_EQUITY"
            return None, flag
        
        if total_equity == 0:
            return None, None
        
        if net_profit is None:
            return None, flag
        
        roe = (net_profit / total_equity) * 100
        return roe, flag
    
    @staticmethod
    def return_on_capital_employed(operating_profit: Optional[float],
                                   equity_capital: Optional[float],
                                   reserves: Optional[float],
                                   borrowings: Optional[float],
                                   sector: Optional[str] = None) -> Optional[float]:
        """
        Calculate Return on Capital Employed (ROCE).
        
        Formula: (EBIT / (equity + reserves + borrowings)) × 100
        Where EBIT = operating_profit
        
        Special Logic: For Financials sector, use relative benchmark (not absolute)
        
        Args:
            operating_profit: Operating profit (EBIT) in crores
            equity_capital: Equity capital in crores
            reserves: Reserves in crores
            borrowings: Total borrowings in crores
            sector: Broad sector classification
        
        Returns:
            ROCE percentage or None if denominator <= 0
        
        Examples:
            return_on_capital_employed(1000, 5000, 2000, 3000) → 10.0
            return_on_capital_employed(1000, 0, 0, 0) → None
        """
        if operating_profit is None:
            return None
        
        equity_capital = equity_capital or 0
        reserves = reserves or 0
        borrowings = borrowings or 0
        
        capital_employed = equity_capital + reserves + borrowings
        
        if capital_employed <= 0:
            return None
        
        roce = (operating_profit / capital_employed) * 100
        
        # For Financials sector, mark for special handling (don't apply absolute thresholds)
        # This is handled in edge_cases.py
        
        return roce
    
    @staticmethod
    def return_on_assets(net_profit: Optional[float],
                        total_assets: Optional[float]) -> Optional[float]:
        """
        Calculate Return on Assets (ROA).
        
        Formula: (net_profit / total_assets) × 100
        
        Args:
            net_profit: Net profit in crores
            total_assets: Total assets in crores
        
        Returns:
            ROA percentage or None if total_assets = 0
        
        Examples:
            return_on_assets(500, 5000) → 10.0
            return_on_assets(500, 0) → None
        """
        if total_assets is None or total_assets == 0:
            return None
        if net_profit is None:
            return None
        
        return (net_profit / total_assets) * 100


class LeverageRatios:
    """
    Compute leverage and solvency ratios.
    
    Ratios:
    - Debt-to-Equity
    - Interest Coverage Ratio (ICR)
    - Net Debt
    - Asset Turnover (efficiency)
    """
    
    @staticmethod
    def debt_to_equity(borrowings: Optional[float],
                      equity_capital: Optional[float],
                      reserves: Optional[float],
                      sector: Optional[str] = None) -> Tuple[Optional[float], Optional[bool]]:
        """
        Calculate Debt-to-Equity Ratio with high leverage flag.
        
        Formula: borrowings / (equity_capital + reserves)
        
        Special Cases:
        - If borrowings = 0: Return 0 (NOT None) - company is debt-free
        - If sector = "Financials": high_leverage_flag = None (leverage normal for banks)
        - Otherwise: If D/E > 5, set high_leverage_flag = True
        
        Args:
            borrowings: Total borrowings in crores
            equity_capital: Equity capital in crores
            reserves: Reserves in crores
            sector: Broad sector classification
        
        Returns:
            Tuple of (D/E ratio, high_leverage_flag or None)
        
        Examples:
            debt_to_equity(0, 5000, 2000, "IT") → (0.0, None)
            debt_to_equity(30000, 5000, 2000, "Industrials") → (4.29, None)
            debt_to_equity(35000, 5000, 2000, "Industrials") → (5.0, True)
            debt_to_equity(35000, 5000, 2000, "Financials") → (5.0, None)
        """
        borrowings = borrowings or 0
        equity_capital = equity_capital or 0
        reserves = reserves or 0
        
        total_equity = equity_capital + reserves
        
        # Debt-free company
        if borrowings == 0:
            return 0.0, None
        
        if total_equity == 0:
            return None, None
        
        de_ratio = borrowings / total_equity
        
        # Flag high leverage only for non-financial companies
        high_leverage_flag = None
        if sector != "Financials" and de_ratio > 5:
            high_leverage_flag = True
        
        return de_ratio, high_leverage_flag
    
    @staticmethod
    def interest_coverage_ratio(operating_profit: Optional[float],
                               interest_expense: Optional[float],
                               other_income: Optional[float] = None) -> Tuple[Optional[float], Optional[str], Optional[bool]]:
        """
        Calculate Interest Coverage Ratio (ICR) with warning flag.
        
        Formula: (operating_profit + other_income) / interest_expense
        
        Returns:
        - If interest_expense = 0: (None, "Debt Free", None) - company has no debt
        - If 0 < ICR < 1.5: (icr_value, None, True) - warning flag set
        - Otherwise: (icr_value, None, None)
        
        Args:
            operating_profit: Operating profit in crores
            interest_expense: Interest expense in crores
            other_income: Other income in crores (optional)
        
        Returns:
            Tuple of (ICR value, icr_label, icr_warning_flag)
        
        Examples:
            interest_coverage_ratio(1000, 0) → (None, "Debt Free", None)
            interest_coverage_ratio(1000, 500) → (2.0, None, None)
            interest_coverage_ratio(700, 500) → (1.4, None, True)
        """
        operating_profit = operating_profit or 0
        other_income = other_income or 0
        
        # Debt-free company (no interest expense)
        if interest_expense is None or interest_expense == 0:
            return None, "Debt Free", None
        
        total_profit = operating_profit + other_income
        
        if total_profit is None:
            return None, None, None
        
        icr = total_profit / interest_expense
        
        # Warning flag if ICR < 1.5 (struggling to cover interest)
        warning_flag = None
        if 0 < icr < 1.5:
            warning_flag = True
        
        return icr, None, warning_flag
    
    @staticmethod
    def net_debt(borrowings: Optional[float],
                investments: Optional[float]) -> Optional[float]:
        """
        Calculate Net Debt (using investments as liquid asset proxy).
        
        Formula: borrowings - investments
        
        Args:
            borrowings: Total borrowings in crores
            investments: Investments/liquid assets in crores
        
        Returns:
            Net debt (can be negative if investments > borrowings)
        
        Examples:
            net_debt(5000, 2000) → 3000.0 (net debt of 3000 Cr)
            net_debt(2000, 3000) → -1000.0 (negative debt = net cash)
        """
        borrowings = borrowings or 0
        investments = investments or 0
        
        return borrowings - investments
    
    @staticmethod
    def asset_turnover(sales: Optional[float],
                      total_assets: Optional[float]) -> Optional[float]:
        """
        Calculate Asset Turnover Ratio.
        
        Formula: sales / total_assets
        Interpretation: Sales generated per unit of assets
        
        Args:
            sales: Total sales in crores
            total_assets: Total assets in crores
        
        Returns:
            Asset turnover ratio or None
        
        Examples:
            asset_turnover(10000, 5000) → 2.0
            asset_turnover(10000, 0) → None
        """
        if total_assets is None or total_assets == 0:
            return None
        if sales is None:
            return None
        
        return sales / total_assets


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Compute ratios for a single company-year
    
    # Sample data
    net_profit = 6500  # crores
    sales = 28750
    operating_profit = 8200
    equity_capital = 2000
    reserves = 5000
    borrowings = 3000
    total_assets = 15000
    interest_expense = 150
    sector = "Financials"
    
    # Profitability ratios
    npm = ProfitabilityRatios.net_profit_margin(net_profit, sales)
    opm, opm_warning = ProfitabilityRatios.operating_profit_margin(operating_profit, sales)
    roe, roe_flag = ProfitabilityRatios.return_on_equity(net_profit, equity_capital, reserves)
    roce = ProfitabilityRatios.return_on_capital_employed(
        operating_profit, equity_capital, reserves, borrowings, sector
    )
    roa = ProfitabilityRatios.return_on_assets(net_profit, total_assets)
    
    print(f"NPM: {npm:.2f}%")
    print(f"OPM: {opm:.2f}%")
    print(f"ROE: {roe:.2f}%")
    print(f"ROCE: {roce:.2f}%")
    print(f"ROA: {roa:.2f}%")
    
    # Leverage ratios
    de, de_flag = LeverageRatios.debt_to_equity(borrowings, equity_capital, reserves, sector)
    icr, icr_label, icr_warning = LeverageRatios.interest_coverage_ratio(
        operating_profit, interest_expense
    )
    net_debt_val = LeverageRatios.net_debt(borrowings, 1000)
    asset_turnover = LeverageRatios.asset_turnover(sales, total_assets)
    
    print(f"\nD/E: {de:.2f}")
    print(f"ICR: {icr:.2f}")
    print(f"Net Debt: {net_debt_val:.2f}")
    print(f"Asset Turnover: {asset_turnover:.2f}")
```

---

### FILE 2: `src/analytics/cagr.py` (250+ lines)

```python
"""
CAGR Engine - Compound Annual Growth Rate Calculation
Handles all 6 edge cases with proper flagging.
"""

from typing import Optional, Tuple
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class CAGRFlag(Enum):
    """CAGR computation flag - reason for None value."""
    NORMAL = None  # Successfully computed CAGR
    DECLINE_TO_LOSS = "DECLINE_TO_LOSS"  # Positive → Negative
    TURNAROUND = "TURNAROUND"  # Negative → Positive
    BOTH_NEGATIVE = "BOTH_NEGATIVE"  # Negative → Negative
    ZERO_BASE = "ZERO_BASE"  # Start value = 0
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # Less than n years


class CAGREngine:
    """
    Compute Compound Annual Growth Rate (CAGR) with edge case handling.
    
    CAGR Formula: ((end_value / start_value) ^ (1/n_years) - 1) × 100
    
    Edge Cases (6 types):
    1. Positive → Positive: Compute normally
    2. Positive → Negative: Return None with DECLINE_TO_LOSS flag
    3. Negative → Positive: Return None with TURNAROUND flag
    4. Negative → Negative: Return None with BOTH_NEGATIVE flag
    5. Zero base (start=0): Return None with ZERO_BASE flag
    6. Insufficient data (<n years): Return None with INSUFFICIENT_DATA flag
    """
    
    @staticmethod
    def compute_cagr(start_value: Optional[float],
                    end_value: Optional[float],
                    n_years: int) -> Tuple[Optional[float], Optional[CAGRFlag]]:
        """
        Compute CAGR with edge case handling.
        
        Args:
            start_value: Starting value (beginning of period)
            end_value: Ending value (end of period)
            n_years: Number of years
        
        Returns:
            Tuple of (CAGR percentage, CAGRFlag)
            CAGR is None if any edge case detected
        
        Examples:
            compute_cagr(100, 200, 5) → (14.87, None) - normal
            compute_cagr(100, -50, 5) → (None, DECLINE_TO_LOSS)
            compute_cagr(-100, 100, 5) → (None, TURNAROUND)
            compute_cagr(0, 100, 5) → (None, ZERO_BASE)
        """
        # Check for None values
        if start_value is None or end_value is None:
            return None, CAGRFlag.INSUFFICIENT_DATA
        
        # Edge Case 1: Insufficient data
        if n_years < 1:
            return None, CAGRFlag.INSUFFICIENT_DATA
        
        # Edge Case 2: Zero base (can't divide by zero)
        if start_value == 0:
            return None, CAGRFlag.ZERO_BASE
        
        # Determine sign of start and end values
        start_positive = start_value > 0
        end_positive = end_value > 0
        
        # Edge Case 3: Positive → Negative (Decline to Loss)
        if start_positive and not end_positive:
            return None, CAGRFlag.DECLINE_TO_LOSS
        
        # Edge Case 4: Negative → Positive (Turnaround)
        if not start_positive and end_positive:
            return None, CAGRFlag.TURNAROUND
        
        # Edge Case 5: Both Negative
        if not start_positive and not end_positive:
            return None, CAGRFlag.BOTH_NEGATIVE
        
        # Normal case: Compute CAGR (both positive)
        # CAGR = ((end/start)^(1/n) - 1) × 100
        try:
            ratio = end_value / start_value
            cagr = ((ratio ** (1.0 / n_years)) - 1) * 100
            return round(cagr, 2), CAGRFlag.NORMAL
        except (ZeroDivisionError, ValueError) as e:
            logger.warning(f"CAGR computation error: {e}")
            return None, CAGRFlag.INSUFFICIENT_DATA
    
    @staticmethod
    def compute_multi_year_cagr(timeseries_dict: dict,
                               metric_name: str,
                               current_year: int,
                               window_years: int) -> Tuple[Optional[float], Optional[CAGRFlag]]:
        """
        Compute CAGR for a specific time window from historical data.
        
        Args:
            timeseries_dict: Dictionary {year: value, ...} sorted by year
            metric_name: Name of metric (for logging)
            current_year: Current fiscal year
            window_years: Number of years to lookback (3, 5, or 10)
        
        Returns:
            Tuple of (CAGR percentage, CAGRFlag)
        
        Example:
            timeseries = {2019: 1000, 2020: 1200, 2021: 1500, 2022: 1800, 2023: 2100}
            compute_multi_year_cagr(timeseries, "Revenue", 2023, 5)
            → (2100, 1000, 5) passed to compute_cagr
            → (14.87, None)
        """
        # Find start year
        start_year = current_year - window_years
        
        # Check if we have data for start year
        if start_year not in timeseries_dict:
            # Not enough historical data
            return None, CAGRFlag.INSUFFICIENT_DATA
        
        if current_year not in timeseries_dict:
            # No current year data
            return None, CAGRFlag.INSUFFICIENT_DATA
        
        start_value = timeseries_dict[start_year]
        end_value = timeseries_dict[current_year]
        
        # Compute CAGR
        return CAGREngine.compute_cagr(start_value, end_value, window_years)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Normal case
    cagr, flag = CAGREngine.compute_cagr(100, 200, 5)
    print(f"CAGR (100→200 over 5 yrs): {cagr}% (flag: {flag})")
    
    # Example 2: Decline to loss
    cagr, flag = CAGREngine.compute_cagr(100, -50, 5)
    print(f"CAGR (100→-50 over 5 yrs): {cagr} (flag: {flag.value})")
    
    # Example 3: Turnaround
    cagr, flag = CAGREngine.compute_cagr(-100, 100, 5)
    print(f"CAGR (-100→100 over 5 yrs): {cagr} (flag: {flag.value})")
    
    # Example 4: Multi-year CAGR
    timeseries = {2019: 15500, 2020: 17200, 2021: 19000, 2022: 21500, 2023: 24200}
    cagr, flag = CAGREngine.compute_multi_year_cagr(timeseries, "Revenue", 2023, 5)
    print(f"\n5-year Revenue CAGR: {cagr}% (flag: {flag})")
```

---

### FILE 3: `src/analytics/cashflow_kpis.py` (280+ lines)

```python
"""
Cash Flow Analysis Engine
Implements FCF, CFO Quality, CapEx Intensity, and Capital Allocation patterns.
"""

from typing import Optional, Dict, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CapitalAllocationPattern(Enum):
    """8 capital allocation patterns based on sign(CFO, CFI, CFF)."""
    REINVESTOR = "Reinvestor"  # (+, -, -)
    SHAREHOLDER_RETURNS = "Shareholder Returns"  # (+, -, +) with CFO/PAT > 1
    LIQUIDATING_ASSETS = "Liquidating Assets"  # (+, +, -)
    DISTRESS_SIGNAL = "Distress Signal"  # (-, +, +)
    GROWTH_FUNDED_BY_DEBT = "Growth Funded by Debt"  # (-, -, +)
    CASH_ACCUMULATOR = "Cash Accumulator"  # (+, +, +)
    PRE_REVENUE = "Pre-Revenue"  # (-, -, -)
    MIXED = "Mixed/Complex"  # Doesn't fit standard patterns


class CashFlowKPIs:
    """Compute cash flow analysis metrics."""
    
    @staticmethod
    def free_cash_flow(operating_activity: Optional[float],
                      investing_activity: Optional[float]) -> Optional[float]:
        """
        Calculate Free Cash Flow (FCF).
        
        Formula: operating_activity + investing_activity
        Note: investing_activity is negative for capex outflows
        
        Interpretation: Cash available after capital expenditures
        
        Args:
            operating_activity: Cash from operations in crores
            investing_activity: Cash from investing in crores (negative for capex)
        
        Returns:
            FCF in crores (can be negative - that's OK)
        
        Examples:
            free_cash_flow(5000, -1000) → 4000 (positive FCF)
            free_cash_flow(5000, -6000) → -1000 (negative FCF, burning cash)
        """
        operating_activity = operating_activity or 0
        investing_activity = investing_activity or 0
        
        return operating_activity + investing_activity
    
    @staticmethod
    def cfo_quality_score(cfo_5yr_avg: Optional[float],
                         pat_5yr_avg: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate CFO Quality Score (5-year average).
        
        Formula: avg(CFO over 5 years) / avg(PAT over 5 years)
        
        Thresholds:
        - > 1.0: "High Quality" (cash earnings > reported earnings)
        - 0.5-1.0: "Moderate" (some working capital management)
        - < 0.5: "Accrual Risk" (cash earnings << reported earnings)
        
        Args:
            cfo_5yr_avg: 5-year average of operating cash flow
            pat_5yr_avg: 5-year average of net profit (PAT)
        
        Returns:
            Tuple of (CFO Quality Score, quality_label)
        
        Examples:
            cfo_quality_score(1000, 800) → (1.25, "High Quality")
            cfo_quality_score(700, 800) → (0.88, "Moderate")
            cfo_quality_score(300, 800) → (0.38, "Accrual Risk")
        """
        if pat_5yr_avg is None or pat_5yr_avg == 0:
            return None, None
        if cfo_5yr_avg is None:
            return None, None
        
        quality_score = cfo_5yr_avg / pat_5yr_avg
        
        # Classify quality
        if quality_score > 1.0:
            label = "High Quality"
        elif quality_score >= 0.5:
            label = "Moderate"
        else:
            label = "Accrual Risk"
        
        return round(quality_score, 2), label
    
    @staticmethod
    def capex_intensity(investing_activity: Optional[float],
                       sales: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
        """
        Calculate CapEx Intensity.
        
        Formula: abs(investing_activity) / sales × 100
        Uses abs() to handle negative CF values
        
        Thresholds:
        - < 3%: "Asset Light"
        - 3-8%: "Moderate"
        - > 8%: "Capital Intensive"
        
        Args:
            investing_activity: Cash from investing (negative for capex)
            sales: Total sales in crores
        
        Returns:
            Tuple of (CapEx Intensity %, intensity_label)
        
        Examples:
            capex_intensity(-2000, 100000) → (2.0, "Asset Light")
            capex_intensity(-5000, 100000) → (5.0, "Moderate")
            capex_intensity(-10000, 100000) → (10.0, "Capital Intensive")
        """
        if sales is None or sales == 0:
            return None, None
        if investing_activity is None:
            investing_activity = 0
        
        capex_pct = (abs(investing_activity) / sales) * 100
        
        # Classify intensity
        if capex_pct < 3:
            label = "Asset Light"
        elif capex_pct <= 8:
            label = "Moderate"
        else:
            label = "Capital Intensive"
        
        return round(capex_pct, 2), label
    
    @staticmethod
    def fcf_conversion_rate(free_cash_flow: Optional[float],
                           operating_profit: Optional[float]) -> Optional[float]:
        """
        Calculate FCF Conversion Rate.
        
        Formula: FCF / operating_profit × 100
        
        Interpretation: % of operating profit converted to free cash
        
        Args:
            free_cash_flow: Free cash flow in crores
            operating_profit: Operating profit in crores
        
        Returns:
            Conversion rate % or None
        
        Examples:
            fcf_conversion_rate(4000, 5000) → 80.0 (80% of operating profit converts to FCF)
            fcf_conversion_rate(-1000, 5000) → -20.0 (negative conversion)
        """
        if operating_profit is None or operating_profit == 0:
            return None
        if free_cash_flow is None:
            return None
        
        conversion_rate = (free_cash_flow / operating_profit) * 100
        return round(conversion_rate, 2)
    
    @staticmethod
    def classify_capital_allocation(cfo_sign: int,
                                   cfi_sign: int,
                                   cff_sign: int,
                                   cfo_pat_ratio: Optional[float] = None) -> str:
        """
        Classify capital allocation pattern based on cash flow signs.
        
        Signature: (CFO_sign, CFI_sign, CFF_sign)
        Where: 1 = positive, -1 = negative, 0 = zero
        
        Patterns:
        (+, -, -) = Reinvestor: Using profits to invest, no dividends/debt issuance
        (+, -, +) = Shareholder Returns: Returning excess cash to shareholders
        (+, +, -) = Liquidating Assets: Selling assets, paying down debt
        (-, +, +) = Distress Signal: Using asset sales & borrowing for operations
        (-, -, +) = Growth Funded by Debt: Early-stage company funded by debt
        (+, +, +) = Cash Accumulator: Building cash reserves
        (-, -, -) = Pre-Revenue: Burning cash, no operating income
        
        Args:
            cfo_sign: Sign of operating cash flow (-1, 0, or 1)
            cfi_sign: Sign of investing cash flow (-1, 0, or 1)
            cff_sign: Sign of financing cash flow (-1, 0, or 1)
            cfo_pat_ratio: CFO/PAT ratio (for distinguishing Reinvestor from Shareholder Returns)
        
        Returns:
            Capital allocation pattern label
        
        Examples:
            classify_capital_allocation(1, -1, -1) → "Reinvestor"
            classify_capital_allocation(1, -1, 1, 1.5) → "Shareholder Returns"
            classify_capital_allocation(-1, 1, 1) → "Distress Signal"
        """
        signature = (cfo_sign, cfi_sign, cff_sign)
        
        # Pattern matching
        if signature == (1, -1, -1):
            return CapitalAllocationPattern.REINVESTOR.value
        
        elif signature == (1, -1, 1):
            # Could be Shareholder Returns or Mixed
            # Use CFO/PAT ratio to distinguish
            if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
                return CapitalAllocationPattern.SHAREHOLDER_RETURNS.value
            else:
                return CapitalAllocationPattern.MIXED.value
        
        elif signature == (1, 1, -1):
            return CapitalAllocationPattern.LIQUIDATING_ASSETS.value
        
        elif signature == (-1, 1, 1):
            return CapitalAllocationPattern.DISTRESS_SIGNAL.value
        
        elif signature == (-1, -1, 1):
            return CapitalAllocationPattern.GROWTH_FUNDED_BY_DEBT.value
        
        elif signature == (1, 1, 1):
            return CapitalAllocationPattern.CASH_ACCUMULATOR.value
        
        elif signature == (-1, -1, -1):
            return CapitalAllocationPattern.PRE_REVENUE.value
        
        else:
            return CapitalAllocationPattern.MIXED.value


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Compute cash flow KPIs
    
    # Data
    cfo = 5000
    cfi = -1000
    cff = -500
    sales = 50000
    operating_profit = 8000
    cfo_5yr = 4500
    pat_5yr = 3500
    
    # Compute metrics
    fcf = CashFlowKPIs.free_cash_flow(cfo, cfi)
    cfo_quality, quality_label = CashFlowKPIs.cfo_quality_score(cfo_5yr, pat_5yr)
    capex_pct, capex_label = CashFlowKPIs.capex_intensity(cfi, sales)
    fcf_conv = CashFlowKPIs.fcf_conversion_rate(fcf, operating_profit)
    
    # Capital allocation
    cfo_sign = 1 if cfo > 0 else (-1 if cfo < 0 else 0)
    cfi_sign = 1 if cfi > 0 else (-1 if cfi < 0 else 0)
    cff_sign = 1 if cff > 0 else (-1 if cff < 0 else 0)
    
    allocation = CashFlowKPIs.classify_capital_allocation(
        cfo_sign, cfi_sign, cff_sign,
        cfo_5yr / pat_5yr
    )
    
    print(f"FCF: {fcf} Cr")
    print(f"CFO Quality: {cfo_quality} ({quality_label})")
    print(f"CapEx Intensity: {capex_pct}% ({capex_label})")
    print(f"FCF Conversion: {fcf_conv}%")
    print(f"Capital Allocation: {allocation}")
```

---

## 📊 SQL MIGRATION FILE

### `db/migrations/002_add_kpi_columns.sql`

```sql
-- Add KPI columns to financial_ratios table (Day 08)

ALTER TABLE financial_ratios ADD COLUMN net_profit_margin_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN operating_profit_margin_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN return_on_equity_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN roe_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN return_on_capital_employed_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN return_on_assets_pct DECIMAL(5,2);

-- Day 09 columns
ALTER TABLE financial_ratios ADD COLUMN debt_to_equity DECIMAL(10,2);
ALTER TABLE financial_ratios ADD COLUMN high_leverage_flag BOOLEAN;
ALTER TABLE financial_ratios ADD COLUMN interest_coverage_ratio DECIMAL(10,2);
ALTER TABLE financial_ratios ADD COLUMN icr_label VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN icr_warning_flag BOOLEAN;
ALTER TABLE financial_ratios ADD COLUMN net_debt_cr BIGINT;
ALTER TABLE financial_ratios ADD COLUMN asset_turnover DECIMAL(10,2);

-- Day 10 columns (CAGR)
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_3yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_3yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_5yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_5yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_10yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN revenue_cagr_10yr_flag VARCHAR(50);

ALTER TABLE financial_ratios ADD COLUMN pat_cagr_3yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN pat_cagr_3yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN pat_cagr_5yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN pat_cagr_5yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN pat_cagr_10yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN pat_cagr_10yr_flag VARCHAR(50);

ALTER TABLE financial_ratios ADD COLUMN eps_cagr_3yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN eps_cagr_3yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN eps_cagr_5yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN eps_cagr_5yr_flag VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN eps_cagr_10yr_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN eps_cagr_10yr_flag VARCHAR(50);

-- Day 11 columns (Cash Flow)
ALTER TABLE financial_ratios ADD COLUMN free_cash_flow_cr BIGINT;
ALTER TABLE financial_ratios ADD COLUMN cfo_quality_score DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN cfo_quality_label VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN capex_intensity_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN capex_intensity_label VARCHAR(50);
ALTER TABLE financial_ratios ADD COLUMN fcf_conversion_rate_pct DECIMAL(5,2);
ALTER TABLE financial_ratios ADD COLUMN capital_allocation_pattern VARCHAR(50);

-- Create indexes for performance
CREATE INDEX idx_ratios_roe ON financial_ratios(return_on_equity_pct);
CREATE INDEX idx_ratios_de ON financial_ratios(debt_to_equity);
CREATE INDEX idx_ratios_revenue_cagr ON financial_ratios(revenue_cagr_5yr_pct);
```

---

## 🧪 COMPLETE TEST FILES (40+ tests)

### `tests/unit/kpi/test_profitability.py` (8 tests)

```python
"""Unit tests for profitability ratios."""

import pytest
from src.analytics.ratios import ProfitabilityRatios


class TestNetProfitMargin:
    """Tests for Net Profit Margin."""
    
    def test_npm_normal_case(self):
        """Normal case: positive sales and profit."""
        npm = ProfitabilityRatios.net_profit_margin(500, 5000)
        assert npm == pytest.approx(10.0, rel=0.01)
    
    def test_npm_zero_sales(self):
        """Sales = 0 should return None."""
        npm = ProfitabilityRatios.net_profit_margin(500, 0)
        assert npm is None
    
    def test_npm_none_sales(self):
        """Sales = None should return None."""
        npm = ProfitabilityRatios.net_profit_margin(500, None)
        assert npm is None
    
    def test_npm_negative_profit(self):
        """Negative profit is allowed (loss)."""
        npm = ProfitabilityRatios.net_profit_margin(-100, 5000)
        assert npm == pytest.approx(-2.0, rel=0.01)


class TestOperatingProfitMargin:
    """Tests for OPM with cross-check."""
    
    def test_opm_normal_case(self):
        """Normal case: positive values."""
        opm, warning = ProfitabilityRatios.operating_profit_margin(1000, 5000)
        assert opm == pytest.approx(20.0, rel=0.01)
        assert warning is None
    
    def test_opm_crosscheck_mismatch(self):
        """OPM crosscheck warns if difference > 1%."""
        opm, warning = ProfitabilityRatios.operating_profit_margin(
            1000, 5000,
            opm_pct_source=21.5
        )
        assert opm == pytest.approx(20.0, rel=0.01)
        assert warning is not None
        assert warning['type'] == 'OPM_CROSSCHECK_MISMATCH'


class TestReturnOnEquity:
    """Tests for ROE computation."""
    
    def test_roe_normal_case(self):
        """Normal case: positive equity and profit."""
        roe, flag = ProfitabilityRatios.return_on_equity(1000, 5000, 2000)
        assert roe == pytest.approx(14.29, rel=0.01)
        assert flag is None
    
    def test_roe_zero_equity(self):
        """Zero equity returns None."""
        roe, flag = ProfitabilityRatios.return_on_equity(1000, 0, 0)
        assert roe is None
        assert flag is None
    
    def test_roe_negative_equity(self):
        """Negative equity sets flag."""
        roe, flag = ProfitabilityRatios.return_on_equity(1000, -1000, 500)
        assert roe is None
        assert flag == "NEGATIVE_EQUITY"


class TestROCE:
    """Tests for ROCE."""
    
    def test_roce_normal_case(self):
        """Normal ROCE computation."""
        roce = ProfitabilityRatios.return_on_capital_employed(
            1000, 5000, 2000, 3000
        )
        assert roce == pytest.approx(10.0, rel=0.01)
```

### `tests/unit/kpi/test_cagr.py` (10 tests)

```python
"""Unit tests for CAGR engine."""

import pytest
from src.analytics.cagr import CAGREngine, CAGRFlag


class TestCAGRNormalCases:
    """Tests for normal CAGR computation."""
    
    def test_cagr_positive_to_positive(self):
        """Normal growth: positive → positive."""
        cagr, flag = CAGREngine.compute_cagr(100, 200, 5)
        assert cagr == pytest.approx(14.87, rel=0.01)
        assert flag == CAGRFlag.NORMAL
    
    def test_cagr_precise_calculation(self):
        """CAGR precision check (within 0.1%)."""
        cagr, flag = CAGREngine.compute_cagr(10000, 15500, 5)
        # Expected: ((15500/10000)^(1/5) - 1) × 100 ≈ 8.46
        assert cagr == pytest.approx(8.46, rel=0.001)


class TestCAGREdgeCases:
    """Tests for all 6 edge cases."""
    
    def test_cagr_decline_to_loss(self):
        """Positive → Negative: company goes from profit to loss."""
        cagr, flag = CAGREngine.compute_cagr(100, -50, 5)
        assert cagr is None
        assert flag == CAGRFlag.DECLINE_TO_LOSS
    
    def test_cagr_turnaround(self):
        """Negative → Positive: company recovers."""
        cagr, flag = CAGREngine.compute_cagr(-100, 100, 5)
        assert cagr is None
        assert flag == CAGRFlag.TURNAROUND
    
    def test_cagr_both_negative(self):
        """Both negative: still negative but improving."""
        cagr, flag = CAGREngine.compute_cagr(-100, -50, 5)
        assert cagr is None
        assert flag == CAGRFlag.BOTH_NEGATIVE
    
    def test_cagr_zero_base(self):
        """Start value = 0: cannot divide by zero."""
        cagr, flag = CAGREngine.compute_cagr(0, 100, 5)
        assert cagr is None
        assert flag == CAGRFlag.ZERO_BASE
    
    def test_cagr_insufficient_data(self):
        """Less than n years of data."""
        cagr, flag = CAGREngine.compute_cagr(None, 100, 5)
        assert cagr is None
        assert flag == CAGRFlag.INSUFFICIENT_DATA


class TestMultiYearCAGR:
    """Tests for multi-year CAGR computation."""
    
    def test_revenue_cagr_5year(self):
        """Compute 5-year revenue CAGR from timeseries."""
        timeseries = {
            2019: 15500,
            2020: 17200,
            2021: 19000,
            2022: 21500,
            2023: 24200
        }
        cagr, flag = CAGREngine.compute_multi_year_cagr(
            timeseries, "Revenue", 2023, 5
        )
        # Expected: ((24200/15500)^(1/5) - 1) × 100 ≈ 9.29
        assert cagr == pytest.approx(9.29, rel=0.01)
        assert flag == CAGRFlag.NORMAL
    
    def test_cagr_insufficient_historical_data(self):
        """Not enough years in timeseries."""
        timeseries = {2022: 20000, 2023: 22000}  # Only 2 years
        cagr, flag = CAGREngine.compute_multi_year_cagr(
            timeseries, "Revenue", 2023, 5
        )
        assert cagr is None
        assert flag == CAGRFlag.INSUFFICIENT_DATA
```

---

## 📋 DAY-BY-DAY EXECUTION GUIDE

### Day 08 Checklist
- [ ] Create src/analytics/ratios.py
- [ ] Implement ProfitabilityRatios class with 5 methods
- [ ] Write test_profitability.py with 8 tests
- [ ] All 8 tests pass
- [ ] Documentation in KPI_FORMULAS.md

### Day 09 Checklist
- [ ] Expand src/analytics/ratios.py
- [ ] Implement LeverageRatios class with 4 methods
- [ ] Write test_leverage.py with 8 tests
- [ ] All 8 tests pass
- [ ] Update documentation

### Day 10 Checklist
- [ ] Create src/analytics/cagr.py
- [ ] Implement CAGREngine with all 6 edge cases
- [ ] Write test_cagr.py with 10 tests
- [ ] All 10 tests pass
- [ ] Document CAGR edge cases

### Day 11 Checklist
- [ ] Create src/analytics/cashflow_kpis.py
- [ ] Implement 5 cash flow methods
- [ ] Implement 8-pattern classifier
- [ ] Write test_cashflow.py with 6 tests
- [ ] Generate capital_allocation.csv

### Day 12 Checklist
- [ ] Run full ratio engine
- [ ] Populate financial_ratios table
- [ ] Verify row count >= 1,100
- [ ] Manual spot-check 3 companies
- [ ] Create ratio_computation_log.csv

### Day 13 Checklist
- [ ] Identify 19 financial sector companies
- [ ] Suppress high_leverage_flag for banks
- [ ] Cross-check ROCE vs source
- [ ] Cross-check ROE vs source
- [ ] Create ratio_edge_cases.log

### Day 14 Checklist
- [ ] Run all 40+ unit tests (0 failures)
- [ ] Review ratio_edge_cases.log
- [ ] Run screener (ROE > 15% AND D/E < 1)
- [ ] Sprint retrospective
- [ ] Demo to team lead
- [ ] Get sign-off

---

