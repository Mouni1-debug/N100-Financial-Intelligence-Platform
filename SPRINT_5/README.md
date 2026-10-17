# N100 Financial Intelligence Platform - Sprint 5
**Intelligence, NLP & PDF Reports** | Days 29-35 | Epics 07, 08 & 09 | Target 70 SP | Due 16 Oct 2026

Python implementation of every Sprint 5 task: analysis-text parser, automatic pros/cons
engine (12 + 12 rules), cash-flow intelligence, capital-allocation report, two-page company
tearsheets, sector PDFs and the portfolio summary PDF.

## Project structure
```
n100_sprint5/
├── run_sprint5.py                  # CLI entry point (--day 29..35 | all)
├── config/settings.py              # ALL paths, thresholds, labels
├── src/
│   ├── utils/        data_loader.py, helpers.py, logger.py, pdf_utils.py, sample_data.py
│   ├── nlp/          parser.py (Day 29), pros_cons_generator.py (Day 30)
│   ├── analytics/    cashflow_kpis.py (Day 31), capital_allocation.py (Day 32), kpi_summary.py
│   ├── reports/      tearsheet.py (33/34), sector_report.py (34), portfolio_summary.py (35),
│   │                 charts.py, styles.py
│   └── pipeline.py                 # run_day29 ... run_day35
├── scripts/          generate_sample_data.py, verify_exit_criteria.py, render_previews.py
├── tests/            helpers, parser, pros/cons, cash flow, reports (20 tests)
├── data/raw|processed/             # INPUTS (analysis.xlsx, companies.csv, ...)  see docs/DATA_SCHEMA.md
├── output/                         # CSV / XLSX deliverables
├── reports/tearsheets|sector|portfolio|tearsheets_test/   # PDF deliverables
├── docs/DATA_SCHEMA.md
└── logs/sprint5.log
```

## Quick start
```bash
pip install -r requirements.txt
python run_sprint5.py --sample-data --day all   # demo with SYNTHETIC data
python scripts/verify_exit_criteria.py          # automated Definition-of-Done check
```
With real data: copy the Sprint 1-4 outputs into `data/processed/` and `data/raw/analysis.xlsx`
(see `docs/DATA_SCHEMA.md`), then `python run_sprint5.py --day all`.
Single day: `python run_sprint5.py --day 30`. Layout test on chosen tickers: `python run_sprint5.py --day 33 --tickers TCS INFY`.

> The files currently in `data/`, `output/` and `reports/` were produced from **synthetic sample data**
> (fictional numbers, real company names). Run `make clean` and load real data before presenting.

## Day -> file -> deliverable map
| Day | Code | Output |
|---|---|---|
| 29 | `src/nlp/parser.py` | `output/analysis_parsed.csv`, `parse_failures.csv`, `cagr_cross_validation.csv` (flags > 5 pp) |
| 30 | `src/nlp/pros_cons_generator.py` | `output/pros_cons_generated.csv` |
| 31 | `src/analytics/cashflow_kpis.py` | `output/cashflow_intelligence.xlsx`, `distress_alerts.csv` |
| 32 | `src/analytics/capital_allocation.py` | `pattern_distribution.csv`, `pattern_changes.csv`, `capital_allocation_gaps.csv` + allocation column in the workbook |
| 33 | `src/reports/tearsheet.py` | `reports/tearsheets_test/` (TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL) |
| 34 | `tearsheet.py`, `sector_report.py` | `reports/tearsheets/{TICKER}_tearsheet.pdf`, `reports/sector/{Sector}_report.pdf`, `output/skipped_tearsheets.csv` |
| 35 | `src/reports/portfolio_summary.py` | `reports/portfolio/portfolio_summary.pdf` |

## How the quality gates are met
* **Confidence** = (60 + 40 x signal strength) x data coverage; only values > 60 are written.
* **>= 1 pro and 1 con per company** - if no rule qualifies, a clearly marked sector-relative
  statement (`PRO_FB` / `CON_FB`, confidence 61) is added; `verify_coverage()` proves it.
* **No text overflow** - all table cells are word-wrapping Paragraphs with fixed column widths,
  very long tokens are soft-broken, and each tearsheet page sits in `KeepInFrame(mode='shrink')`
  so content can never create a 3rd page; the shrink factor is checked and logged.
* **No blank pages / 2 pages / >= 30 KB** - checked automatically by `verify_exit_criteria.py`.

## Interpretation notes (please confirm with the team lead)
1. **File names** - the sprint text lost the placeholders; used `{TICKER}_tearsheet.pdf` and `{Sector}_report.pdf`
   (special characters become `_`, e.g. `M&M` -> `M_M_tearsheet.pdf`).
2. **Pro Rule 11** - title says "Revenue CAGR > PAT CAGR" but the text says revenue grows *slower* than profit.
   The **text** (PAT CAGR > Revenue CAGR = operating leverage) is implemented.
3. **Regex** - spec pattern extended with an optional minus sign so negative growth is captured.
   "Divergence > 5%" is read as **5 percentage points**.
4. **Pro/Con rules on financials** - D/E, ICR, OPM, ROCE, net-debt and borrowing rules are skipped for banks/NBFCs.
5. **CFO quality** - years with PAT <= 0 are excluded from the 5-year average (ratio not meaningful).
   **CapEx intensity** uses the latest year.
6. **Trend arrows** - up = *improved*, so a falling Debt/Equity shows an up arrow; flat = within +/-2 %.
7. **Currency / arrows** - PDFs use "Rs Cr" and vector-drawn arrows because the built-in PDF fonts have no rupee or arrow glyphs.
8. Tearsheets need >= 3 years of data; others are logged to `output/skipped_tearsheets.csv`.

## Still manual (per Definition of Done)
Visual review of 5 tearsheets (`python scripts/render_previews.py` creates PNGs), Sprint 5 retrospective,
demo and team-lead sign-off.
