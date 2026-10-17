import pandas as pd

from src.analytics import capital_allocation
from src.analytics.cashflow_kpis import (SPEC_COLUMNS, capex_label, cfo_quality_label,
                                         compute_cashflow_kpis, distress_alerts)


def test_label_boundaries():
    assert cfo_quality_label(1.2) == "High Quality"
    assert cfo_quality_label(1.0) == "Moderate"
    assert cfo_quality_label(0.5) == "Moderate"
    assert cfo_quality_label(0.49) == "Accrual Risk"
    assert capex_label(2.9) == "Asset Light"
    assert capex_label(3) == "Moderate" and capex_label(8) == "Moderate"
    assert capex_label(8.1) == "Capital Intensive"


def test_table_has_every_company_and_spec_columns(store):
    full = compute_cashflow_kpis(store)
    assert len(full) == len(store.companies)
    assert set(SPEC_COLUMNS) <= set(full.columns)


def test_distress_definition(store):
    full = compute_cashflow_kpis(store)
    flagged = full[full["distress_flag"]]
    assert ((flagged["latest_cfo"] < 0) & (flagged["latest_cff"] > 0)).all()
    alerts = distress_alerts(full)
    assert {"cfo_value", "cff_value", "latest_net_profit"} <= set(alerts.columns)


def test_capital_allocation_helpers(store):
    ca = store.table("capital_allocation")
    assert capital_allocation.validate_completeness(ca, store.fundamentals).empty
    dist = capital_allocation.distribution(ca, store.latest_year)
    assert len(dist) >= 8 and dist["companies"].sum() == ca[ca["year"] == store.latest_year].shape[0]
    changes = capital_allocation.pattern_changes(ca, store.companies)
    assert (changes["from_pattern"] != changes["to_pattern"]).all()
