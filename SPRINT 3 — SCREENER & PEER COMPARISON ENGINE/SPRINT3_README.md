# N100 Sprint 3 - Screener & Peer Comparison Engine

A comprehensive financial screener and peer comparison system for Nifty 100 companies.

## Features

### Screener Engine
- **15 Filterable Metrics**: ROE, D/E, FCF, Revenue/PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR, Market Cap, Net Profit, EPS CAGR, Asset Turnover, Sales
- **Special Handling**: D/E filter excludes Financials sector; ICR filter treats Debt Free as infinity
- **Custom Filtering**: Create your own filter combinations

### 6 Preset Screeners
1. **Quality Compounder**: ROE>15%, D/E<1, FCF>0, Revenue CAGR>10% → 10-30 companies
2. **Value Pick**: P/E<20, P/B<3, D/E<2, Dividend Yield>1% → 15-40 companies
3. **Growth Accelerator**: PAT CAGR>20%, Revenue CAGR>15%, D/E<2 → 5-20 companies
4. **Dividend Champion**: Dividend Yield>2%, Payout<80%, FCF>0 → 10-25 companies
5. **Debt-Free Blue Chip**: D/E=0, ROE>12%, Revenue>5000Cr → 5-15 companies
6. **Turnaround Watch**: Revenue CAGR 3yr>10%, FCF>0, D/E declining → 10-30 companies

### Composite Quality Score (0-100 scale)
- **35% Profitability**: ROE(15%) + ROCE(10%) + NPM(10%)
- **30% Cash Quality**: FCF CAGR(15%) + CFO/PAT(10%) + FCF flag(5%)
- **20% Growth**: Revenue CAGR 5yr(10%) + PAT CAGR 5yr(10%)
- **15% Leverage**: D/E score(10%) + ICR score(5%)
- P10/P90 winsorisation for extreme value handling
- Sector-relative scoring for peer comparison

### Peer Percentile Rankings
- **10 Metrics Ranked**: ROE, ROCE, NPM, D/E (inverted), FCF, PAT CAGR 5yr, Revenue CAGR 5yr, EPS CAGR 5yr, ICR, Asset Turnover
- **11 Peer Groups**: IT Services, FMCG, Pharma, Banking, Auto, Metals & Mining, Oil & Gas, Power, Telecom, Infrastructure, Financials
- Percentile rank 0-100 within peer group
- Handles companies with no peer group assignment

### Radar Charts
- **8-Axis Visualization**: ROE, ROCE, NPM, D/E (inverted), FCF Score, PAT CAGR 5yr, Revenue CAGR 5yr, Composite Score
- Company polygon + peer group average dashed overlay
- 150 DPI quality for web/print
- 92 PNG files (one per company)

### Excel Reports
- **screener_output.xlsx**: 6 sheets (one per preset), 20 KPI columns, color-coded
- **peer_comparison.xlsx**: 11 sheets (one per peer group), percentile color-coded, summary rows

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/n100-sprint3-screener-peer-engine.git
cd n100-sprint3-screener-peer-engine

# Install dependencies
make install

# Or: pip install -r requirements.txt
```

## Setup Database

```bash
# Apply migration
sqlite3 db/nifty100.db < db/migrations/003_add_peer_percentiles.sql

# Verify table created
sqlite3 db/nifty100.db "SELECT COUNT(*) FROM peer_percentiles;"
```

## Usage

### Run Screener
```bash
python scripts/run_screener.py
# Outputs: data/output/screener_output.xlsx (6 sheets)
```

### Generate Peer Report
```bash
python scripts/generate_peer_report.py
# Outputs: data/output/peer_comparison.xlsx (11 sheets)
```

### Generate Radar Charts
```bash
python scripts/generate_radar_charts.py
# Outputs: reports/radar_charts/*.png (92 files)
```

### Run Tests
```bash
make test
# Or: pytest tests/unit/screener/ -v

# With coverage
make test-coverage
```

### Makefile Commands
```bash
make install          # Install dependencies
make test             # Run all tests
make test-coverage    # Run tests with coverage report
make run              # Run full screener pipeline
make clean            # Clean temp files
make lint             # Lint code (if configured)
```

## Project Structure

```
n100-sprint3-screener-peer-engine/
├── src/
│   ├── screener/
│   │   ├── engine.py           # Filter engine (15 metrics)
│   │   ├── presets.py          # 6 preset screeners
│   │   ├── composite_score.py  # Quality score calculator
│   │   └── validators.py       # Data validation
│   └── analytics/
│       ├── peer.py             # Percentile ranking engine
│       └── visualization.py    # Radar chart generator
├── db/
│   ├── schema.sql              # Base schema
│   └── migrations/
│       └── 003_add_peer_percentiles.sql
├── data/output/                # Generated outputs
├── reports/radar_charts/       # PNG charts
├── config/
│   ├── screener_config.yaml    # Filter configuration
│   ├── peer_groups.xlsx        # Peer mappings
│   └── logging.yaml            # Logging config
├── tests/unit/screener/        # 31 unit tests
├── scripts/
│   ├── run_screener.py
│   ├── generate_peer_report.py
│   ├── generate_radar_charts.py
│   └── validate_screener.py
└── docs/                       # Design documentation
```

## Configuration

Edit `config/screener_config.yaml` to customize:
- Filter thresholds (15 metrics)
- Preset criteria
- Composite score weights
- Exclusions and special cases

## Database

### peer_percentiles Table
```sql
CREATE TABLE peer_percentiles (
    peer_id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL,
    peer_group_name VARCHAR(100),
    metric VARCHAR(100),
    value DECIMAL(10,2),
    percentile_rank DECIMAL(5,2),
    fiscal_year INTEGER,
    created_at TIMESTAMP,
    UNIQUE(company_id, peer_group_name, metric, fiscal_year)
);
```

- **1,000+ rows** populated
- **10 metrics** per company per peer group
- **11 peer groups** supported

## Testing

### Unit Tests
- **test_filter_engine.py** (8 tests): Filter logic validation
- **test_presets.py** (6 tests): Preset criteria verification
- **test_composite_score.py** (6 tests): Score calculation
- **test_peer_rankings.py** (6 tests): Percentile ranking
- **test_screener_integration.py** (5 tests): End-to-end workflow

### Coverage: 85%+

Run tests:
```bash
pytest tests/unit/screener/ -v
pytest tests/unit/screener/ -v --cov=src/screener --cov=src/analytics
```

## Example Usage

### Python API

```python
import pandas as pd
from src.screener.engine import ScreenerEngine
from src.screener.presets import ScreenerPresets
from src.screener.composite_score import CompositeScoreCalculator

# Load financial data
df = pd.read_sql("SELECT * FROM financial_ratios", conn)

# Calculate composite scores
calculator = CompositeScoreCalculator(config)
df = calculator.calculate_composite_score(df)

# Initialize screener
engine = ScreenerEngine("config/screener_config.yaml")

# Run preset screener
presets = ScreenerPresets(engine)
quality_companies, metadata = presets.quality_compounder(df)
print(f"Found {len(quality_companies)} quality compounder companies")

# Custom filtering
custom_filters = {
    'roe_min': 20,
    'de_max': 1.5,
    'fcf_min': 500
}
results = engine.screen(df, custom_filters)
results = results.sort_values('composite_quality_score', ascending=False)
results.to_excel('output/custom_screen.xlsx', index=False)
```

### Command Line

```bash
# Full pipeline
python scripts/run_screener.py
python scripts/generate_peer_report.py
python scripts/generate_radar_charts.py

# Generate all outputs
make run

# Validate data quality
python scripts/validate_screener.py
```

## Outputs

### 1. screener_output.xlsx
- 6 sheets (one per preset)
- Columns: company_id, company_name, 20 KPI columns, composite_quality_score
- Sorted by composite_quality_score (descending)
- Color-coded: green = meets threshold, red = fails

### 2. peer_comparison.xlsx
- 11 sheets (one per peer group)
- Columns: company_id, company_name, 20 metrics, percentile_rank
- Color-coded: green ≥75th, yellow 25-75th, red ≤25th
- Summary row showing peer group medians

### 3. Radar Charts (reports/radar_charts/)
- Filename: `{company_id}_radar.png`
- 92 PNG files
- 150 DPI quality
- Company polygon + peer group average overlay

## Design Documents

See `/docs/` for:
- **SCREENER_FORMULAS.md** - All filter formulas
- **COMPOSITE_SCORE_DESIGN.md** - Score calculation logic
- **PEER_RANKING_DESIGN.md** - Percentile ranking methodology
- **VISUALIZATION_GUIDE.md** - Radar chart design
- **IMPLEMENTATION_GUIDE.md** - Step-by-step implementation

## Requirements

- Python 3.7+
- pandas >= 1.3.0
- numpy >= 1.21.0
- scipy >= 1.7.0
- openpyxl >= 3.6.0
- matplotlib >= 3.4.0
- pyyaml >= 5.4.0
- pytest >= 6.2.0 (for testing)

## Exit Criteria (Definition of Done)

✅ 6 preset screeners return 5-50 companies each
✅ peer_comparison.xlsx has exactly 11 sheets
✅ Peer percentile ranks correct (spot-checked IT Services, FMCG)
✅ All 31 unit tests pass (0 failures)
✅ 92 radar charts generated
✅ peer_percentiles table populated (1,000+ rows)
✅ Code follows PEP 8 style guide
✅ All functions documented with docstrings

## Deployment

### GitHub
1. Create repository: `n100-sprint3-screener-peer-engine`
2. Push all files
3. Add README.md, LICENSE, .gitignore
4. Enable GitHub Actions for CI/CD

### Local Development
```bash
git clone <repo>
pip install -r requirements.txt
make test
make run
```

## License

Proprietary - Bluestock Fintech Pvt. Ltd.

## Author

N100 Financial Intelligence Platform
Sprint 3 - Screener & Peer Comparison Engine
Day 15-21 | 49 Story Points | Production Ready

---

**Version**: 1.0.0
**Status**: ✅ Complete & Tested
**Last Updated**: 2026-09-29
