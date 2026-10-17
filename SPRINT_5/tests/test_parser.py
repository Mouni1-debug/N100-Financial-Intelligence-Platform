import pandas as pd

from src.nlp.parser import cross_validate_cagr, parse_analysis, parse_text_cell


def test_basic_extraction():
    matches, failures = parse_text_cell("10 Years: 21%\n5 Years: 18.5%\n3 Years: 15%")
    assert matches == [(10, 21.0), (5, 18.5), (3, 15.0)]
    assert failures == []


def test_negative_and_spacing_variants():
    matches, _ = parse_text_cell("5 Years:-3.2%   1 Year : 4%  10Years: 7%")
    assert (5, -3.2) in matches and (10, 7.0) in matches


def test_unmatched_entries_are_reported():
    matches, failures = parse_text_cell("N/A")
    assert matches == [] and failures == ["N/A"]
    matches, failures = parse_text_cell("5 Years: 12%\nTTM: 9%")
    assert matches == [(5, 12.0)] and failures == ["TTM: 9%"]
    assert parse_text_cell(float("nan"))[1] == ["<empty>"]


def test_parse_analysis_shape():
    df = pd.DataFrame([{"company_id": 1, "compounded_sales_growth": "10 Years: 21%", "compounded_profit_growth": "oops",
                        "stock_price_cagr": "5 Years: 10%", "roe": "3 Years: 25%"}])
    parsed, failures = parse_analysis(df)
    assert list(parsed.columns) == ["company_id", "metric_type", "period_years", "value_pct"]
    assert len(parsed) == 3 and len(failures) == 1
    assert failures.iloc[0]["metric_type"] == "compounded_profit_growth"


def test_cross_validation_flags_gap_over_5pp():
    parsed = pd.DataFrame({"company_id": [1, 1], "metric_type": ["roe", "roe"], "period_years": [5, 3],
                           "value_pct": [20.0, 30.0]})
    engine = pd.DataFrame({"company_id": [1, 1], "metric_type": ["roe", "roe"], "period_years": [5, 3],
                           "value_pct": [18.0, 22.0]})
    out = cross_validate_cagr(parsed, engine)
    flagged = out[out["needs_review"]]
    assert len(flagged) == 1 and flagged.iloc[0]["period_years"] == 3
