# Sprint 4 - Dashboard & Valuation Module

Complete Streamlit dashboard with 8 screens and valuation analysis for Nifty 100 companies.

## Features

### 🏠 Home Screen (pages/01_home.py)
- **6 Summary KPI Tiles**: Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR, Debt-Free Count
- **Sector Breakdown Donut Chart**: 11 sectors with company counts (Plotly)
- **Top 5 Companies Table**: Sorted by composite quality score
- **Year Selector**: 2019-2024 (all metrics update dynamically)

### 👤 Company Profile Screen (pages/02_profile.py)
- **Company Search**: Type company name or ticker - autocomplete dropdown
- **Company Card**: Name, sector, sub-sector, NSE ticker
- **6 KPI Tiles**: ROE, ROCE, NPM, D/E, Revenue CAGR 5yr, FCF
- **10-Year Revenue & Net Profit Bar Charts**: Historical trends
- **ROE vs ROCE Dual-Axis Chart**: 10-year comparison
- **Pros & Cons Badges**: Green checks and red warning signs
- **Load Time**: <3 seconds guaranteed

### 🔍 Screener Screen (pages/03_screener.py)
- **10 Metric Sliders**: ROE, D/E, FCF, Revenue CAGR, PAT CAGR, OPM, P/E, P/B, Dividend Yield, ICR
- **6 Preset Buttons**: Quality, Value, Growth, Dividend, Debt-Free, Turnaround (auto-fills sliders)
- **Live Results Table**: Updates as sliders move
- **Result Count**: Shows number of companies matching filters
- **CSV Download**: Valid CSV with all visible columns and proper headers

### 👥 Peer Comparison Screen (pages/04_peers.py)
- **Peer Group Dropdown**: 11 groups (IT Services, FMCG, Pharma, etc.)
- **Radar Chart**: 8-axis (ROE, ROCE, NPM, D/E, FCF, PAT CAGR, Revenue CAGR, Composite Score)
  - Company polygon (solid)
  - Peer group average overlay (dashed)
- **KPI Table**: All companies in selected group with percentile ranks
- **Benchmark Highlight**: Highest quality score row highlighted

### 📈 Trend Analysis Screen (pages/05_trends.py)
- **Company Search**: Select company
- **Multi-Metric Selector**: Choose up to 3 metrics (Revenue, Net Profit, Operating Profit, EBITDA, FCF)
- **10-Year Line Chart**: With YoY % annotations on each point
- **Summary Stats**: CAGR, 10-year growth, latest YoY growth

### 🏭 Sector Analysis Screen (pages/06_sectors.py)
- **Bubble Chart**: 
  - X-axis: Revenue
  - Y-axis: ROE
  - Bubble size: Market Cap
  - Color: Sub-sector
- **Sector Median KPI Bar Chart**: ROE, ROCE, Net Margin, D/E, Revenue CAGR
- **Company Breakdown Table**: All companies in sector with metrics
- **Summary Metrics**: Company count, total market cap, median ROE

### 💰 Capital Allocation Screen (pages/07_capital.py)
- **Treemap**: 92 companies grouped by 8 capital allocation patterns
- **8 Patterns**:
  1. Reinvestor (positive FCF, negative investing, negative financing)
  2. Shareholder Returns (positive FCF, negative investing, positive financing)
  3. Liquidating Assets (positive FCF, positive investing, negative financing)
  4. Distress Signal (negative FCF, positive investing, positive financing)
  5. Growth Funded by Debt (negative FCF, negative investing, positive financing)
  6. Cash Accumulator (all positive)
  7. Pre-Revenue (all negative)
  8. Mixed/Complex (other combinations)
- **Pattern Explanations**: Expandable cards with descriptions
- **Company Filtering**: View companies by selected pattern

### 📄 Annual Reports Screen (pages/08_reports.py)
- **Company Search**: Find company and view available reports
- **Report List**: All years 2015-2024
- **Availability Status**: ✅ Available or ❌ Unavailable (red badge)
- **File Size**: Shows MB for available reports
- **PDF Links**: Direct BSE download links
- **404 Handling**: Shows "Report unavailable" for missing reports

## Installation & Setup

### Prerequisites
- Python 3.7+
- SQLite3
- pip

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Database Setup
```bash
# Apply valuation migration if needed
sqlite3 db/nifty100.db < db/migrations/004_valuation_table.sql

# Run valuation analysis
python src/analytics/valuation.py
```

### Step 3: Run Dashboard
```bash
streamlit run src/dashboard/app.py
```

Dashboard will open at: `http://localhost:8501`

### Alternative - Using Makefile
```bash
make install
make db-setup
make run-dashboard
```

## File Structure

```
src/
├── dashboard/
│   ├── app.py                          (Main entry point)
│   └── utils/
│       └── db.py                       (Cached data loader)
└── analytics/
    └── valuation.py                    (Valuation engine)

pages/
├── 01_home.py                          (Home screen)
├── 02_profile.py                       (Company profile)
├── 03_screener.py                      (Financial screener)
├── 04_peers.py                         (Peer comparison)
├── 05_trends.py                        (Trend analysis)
├── 06_sectors.py                       (Sector analysis)
├── 07_capital.py                       (Capital allocation)
└── 08_reports.py                       (Annual reports)

data/output/
├── valuation_summary.xlsx              (92 companies, all valuation metrics)
└── valuation_flags.csv                 (Only Caution/Discount flagged companies)

.streamlit/
└── config.toml                         (Streamlit configuration)
```

## Database Schema (New Tables)

### valuation table
```sql
CREATE TABLE valuation (
    valuation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    nse_ticker VARCHAR(10),
    pe_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    ev_ebitda DECIMAL(10,2),
    fcf_yield_pct DECIMAL(5,2),
    sector_median_pe DECIMAL(10,2),
    pe_vs_sector_median_pct DECIMAL(5,2),
    valuation_flag VARCHAR(20),
    flag_reason TEXT,
    fiscal_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, fiscal_year)
);
```

## Valuation Metrics

### FCF Yield (%)
```
Formula: (Free Cash Flow / Market Cap) × 100
Interpretation: Higher = More cash generation relative to valuation
```

### P/E vs Sector Median (%)
```
Formula: ((Company P/E - Sector Median P/E) / Sector Median P/E) × 100
Negative = Undervalued, Positive = Overvalued
```

### Valuation Flags
- **Caution**: P/E > Sector Median × 1.5 (50% above peers)
- **Discount**: P/E < Sector Median × 0.7 (30% below peers)
- **Fair**: Otherwise (within ±50% of sector median)

## Configuration

Edit `src/dashboard/utils/db.py` to customize:
- Database path
- Cache time-to-live (TTL): Currently 600 seconds
- Data query filters

## Performance Optimization

### Streamlit Caching
All data loader functions use `@st.cache_data(ttl=600)`:
- Caches database queries for 10 minutes
- Automatic cache invalidation after TTL
- Manual refresh via Streamlit menu

### Chart Optimization
- Plotly for interactive charts (faster than matplotlib)
- Responsive layout using st.columns
- Dynamic height adjustment

### Load Time Targets
- Home Screen: <2 seconds
- Company Profile: <3 seconds
- Screener: <1 second (live filtering)
- Other screens: <2 seconds

## Testing

### Manual Testing Checklist

**Home Screen**
- [ ] 6 KPI tiles load correctly
- [ ] Sector donut chart renders
- [ ] Year selector updates all metrics
- [ ] Top 5 table shows correct data

**Company Profile**
- [ ] Company search works (autocomplete)
- [ ] All 6 KPI tiles populate
- [ ] 10-year charts display without errors
- [ ] Pros/cons badges appear
- [ ] Ticker not found → friendly error message
- [ ] Load time < 3 seconds

**Screener**
- [ ] All 10 sliders work
- [ ] Presets auto-fill sliders correctly
- [ ] Table updates live as sliders move
- [ ] CSV download produces valid file
- [ ] Result count updates dynamically
- [ ] Extreme values (min/max sliders) don't crash

**Peer Comparison**
- [ ] 11 peer groups in dropdown
- [ ] Radar chart displays company vs peers
- [ ] Percentile ranks calculated correctly
- [ ] Table highlights benchmark company

**Trend Analysis**
- [ ] Company search works
- [ ] Multi-select supports up to 3 metrics
- [ ] Line chart shows YoY % annotations
- [ ] CAGR calculation correct

**Sector Analysis**
- [ ] Bubble chart renders with correct positioning
- [ ] Color by sub-sector works
- [ ] Bubble size represents market cap
- [ ] Sector median bar chart displays
- [ ] Company table filters by sector

**Capital Allocation**
- [ ] Treemap displays all 8 patterns
- [ ] Click expands pattern details
- [ ] Company list filters by pattern
- [ ] Pattern counts accurate

**Annual Reports**
- [ ] Company search works
- [ ] Report list shows 2015-2024
- [ ] Status badges (✅/❌) correct
- [ ] PDF links functional
- [ ] 404 handling shows friendly message
- [ ] File sizes display for available reports

### Test Tickers
- **IT Services**: TCS, Infosys, Wipro
- **Banking**: HDFC Bank, ICICI Bank, Axis Bank
- **Financials**: Bajaj Finance, HDFC
- **FMCG**: ITC, Britannia, Nestlé
- **Auto**: Maruti, M&M, Bajaj Auto
- **Pharma**: Sun Pharma, Dr. Reddy's
- **Energy**: Reliance, NTPC
- **Metals**: Tata Steel, Hindalco

Test with companies having <10 years of data to verify "Data available" notes.

## Exit Criteria (Definition of Done)

✅ All 8 Streamlit screens load without errors for any of 92 tickers
✅ Company Profile screen loads in <3 seconds
✅ Screener CSV download produces valid file with correct headers
✅ valuation_summary.xlsx has 92 rows with all required columns
✅ Sprint 4 review demo completed - team lead sign-off

## Deployment

### Local Development
```bash
streamlit run src/dashboard/app.py
```

### Production (Streamlit Cloud)
```bash
# Deploy to Streamlit Cloud
streamlit deploy
```

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "src/dashboard/app.py"]
```

## Troubleshooting

### Dashboard won't start
```bash
# Clear cache
rm ~/.streamlit/cache
streamlit run src/dashboard/app.py --logger.level=debug
```

### Charts not rendering
- Check Plotly version: `pip install --upgrade plotly`
- Verify browser JavaScript enabled
- Try Chrome/Firefox (Streamlit supports modern browsers)

### Database connection errors
- Verify `db/nifty100.db` exists
- Check file permissions: `chmod 644 db/nifty100.db`
- Run: `sqlite3 db/nifty100.db "SELECT COUNT(*) FROM companies;"`

### Slow load times
- Check network connectivity
- Verify database indexes: `ANALYZE;` in SQLite
- Increase cache TTL in `db.py`: `ttl=1200` (20 minutes)

## Documentation

See `/docs/` for:
- **DASHBOARD_DESIGN.md** - UI/UX decisions
- **VALUATION_METHODOLOGY.md** - FCF yield and P/E analysis
- **PERFORMANCE_GUIDE.md** - Optimization techniques
- **DATA_QUALITY_NOTES.md** - Known issues and limitations

## Version History

- **v1.0.0** (2026-10-12) - Sprint 4 Complete Release
  - All 8 screens fully functional
  - Valuation module integrated
  - Production-ready dashboard

## Support

For issues or questions:
1. Check logs: `tail -f ~/.streamlit/logs`
2. Review data quality: Run `validate_screener.py`
3. Test with sample tickers
4. Contact: yash.kale@bluestock.in

---

**Status**: ✅ Production Ready
**Sprint**: 4 (Day 22-28)
**Story Points**: 55 SP
**Last Updated**: 2026-10-12
