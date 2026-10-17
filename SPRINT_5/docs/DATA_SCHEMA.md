# Input data contract

Sprint 5 reads the outputs of Sprints 1-4. If your column names differ, edit
`REQUIRED_COLUMNS` in `src/utils/data_loader.py` (one place) - the loader raises a clear
`DataValidationError` listing any missing column.

| File | Location | Required columns |
|---|---|---|
| companies.csv | data/processed | company_id, company_name, ticker, sector, is_financial |
| profit_loss.csv | data/processed | company_id, year, sales, operating_profit, opm_pct, net_profit, eps, dividend_payout_pct, interest |
| balance_sheet.csv | data/processed | company_id, year, equity_capital, reserves, borrowings, other_liabilities, total_assets |
| cash_flow.csv | data/processed | company_id, year, operating_activity, investing_activity, financing_activity, net_cash_flow |
| ratios.csv (Ratio Engine) | data/processed | company_id, year, roe_pct, roce_pct, de_ratio, icr, dividend_yield_pct, fcf, ebitda, net_debt |
| ratio_engine_cagr.csv | data/processed | company_id, metric_type, period_years, value_pct |
| capital_allocation.csv (Sprint 2) | data/processed | company_id, year, pattern |
| analysis.xlsx | data/raw | company_id, compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe |

Notes
* `year` is the 4-digit financial year (e.g. 2025). Money columns are in Rs Cr.
* `is_financial` is TRUE for banks / NBFCs / insurers - leverage, ICR, OPM and ROCE based rules are skipped for them.
* `metric_type` in `ratio_engine_cagr.csv` uses the same four names as the analysis.xlsx text columns.
* The 8 capital-allocation pattern names live in `config/settings.py -> CAPITAL_ALLOCATION_PATTERNS`;
  change them to match Sprint 2 exactly.
