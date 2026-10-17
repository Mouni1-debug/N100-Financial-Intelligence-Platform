import pandas as pd

from src.nlp.pros_cons_generator import (RULES, CompanyContext, evaluate_company, generate_pros_cons,
                                         verify_coverage)


def _ctx(roe, **extra):
    years = list(range(2021, 2021 + len(roe)))
    frame = pd.DataFrame({"year": years, "roe_pct": roe, **{k: v for k, v in extra.items()}})
    comp = pd.Series({"company_id": 1, "ticker": "T", "sector": "S", "is_financial": False})
    return CompanyContext(comp, frame)


def test_rule_catalogue_is_12_and_12():
    assert sum(r.kind == "pro" for r in RULES) == 12
    assert sum(r.kind == "con" for r in RULES) == 12
    assert len({r.rule_id for r in RULES}) == 24


def test_pro_rule_1_requires_three_years_above_20():
    hit = evaluate_company(_ctx([18, 24, 26, 29]))
    assert any(r["rule_id"] == "PRO_01" for r in hit)
    miss = evaluate_company(_ctx([30, 18, 26, 29]))
    assert not any(r["rule_id"] == "PRO_01" for r in miss)


def test_confidence_is_always_above_threshold_and_text_formats():
    ctx = _ctx([12, 12, 12, 12, 12], de_ratio=[2.5] * 5)
    rows = evaluate_company(ctx)
    assert all(r["confidence_pct"] > 60 for r in rows)
    con1 = [r for r in rows if r["rule_id"] == "CON_01"][0]
    assert "2.50" in con1["text"] and "{" not in con1["text"]


def test_financials_skip_leverage_rules():
    comp = pd.Series({"company_id": 1, "ticker": "B", "sector": "Banking", "is_financial": True})
    frame = pd.DataFrame({"year": [2024, 2025], "de_ratio": [8.0, 9.0], "roe_pct": [12, 13]})
    rows = evaluate_company(CompanyContext(comp, frame))
    assert not any(r["rule_id"] == "CON_01" for r in rows)


def test_every_company_has_a_pro_and_a_con(store):
    df = generate_pros_cons(store)
    assert verify_coverage(df, store.companies).empty
    assert list(df.columns) == ["company_id", "type", "rule_id", "text", "confidence_pct"]
    assert set(df["type"]) == {"pro", "con"}
    assert (df["confidence_pct"] > 60).all()
