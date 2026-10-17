"""Synthetic dataset generator - lets the whole Sprint 5 pipeline run end-to-end
before (or without) the real Sprint 1-4 outputs.

THE NUMBERS ARE FICTIONAL. Only the company names / tickers / sectors are real
labels so reports look familiar. Replace ``data/processed/*`` and
``data/raw/analysis.xlsx`` with the real Sprint 1-4 outputs for production use.
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from config import settings

# (ticker, company name, sector, is_financial) - 92 companies across 11 sectors
_RAW = """
IT|TCS,Tata Consultancy Services;INFY,Infosys;WIPRO,Wipro;HCLTECH,HCL Technologies;TECHM,Tech Mahindra;LTIM,LTIMindtree;PERSISTENT,Persistent Systems;COFORGE,Coforge
Banking|HDFCBANK,HDFC Bank;ICICIBANK,ICICI Bank;SBIN,State Bank of India;KOTAKBANK,Kotak Mahindra Bank;AXISBANK,Axis Bank;INDUSINDBK,IndusInd Bank;BANKBARODA,Bank of Baroda;PNB,Punjab National Bank;IDFCFIRSTB,IDFC First Bank;FEDERALBNK,Federal Bank
Financial Services|BAJFINANCE,Bajaj Finance;BAJAJFINSV,Bajaj Finserv;HDFCLIFE,HDFC Life Insurance;SBILIFE,SBI Life Insurance;CHOLAFIN,Cholamandalam Investment;SHRIRAMFIN,Shriram Finance;MUTHOOTFIN,Muthoot Finance;ICICIGI,ICICI Lombard General Insurance
Oil & Gas|RELIANCE,Reliance Industries;ONGC,Oil and Natural Gas Corporation;BPCL,Bharat Petroleum;IOC,Indian Oil Corporation;GAIL,GAIL (India);HINDPETRO,Hindustan Petroleum;PETRONET,Petronet LNG;OIL,Oil India
Pharma|SUNPHARMA,Sun Pharmaceutical Industries;DRREDDY,Dr. Reddy's Laboratories;CIPLA,Cipla;DIVISLAB,Divi's Laboratories;LUPIN,Lupin;AUROPHARMA,Aurobindo Pharma;TORNTPHARM,Torrent Pharmaceuticals;ZYDUSLIFE,Zydus Lifesciences
Metals & Mining|TATASTEEL,Tata Steel;JSWSTEEL,JSW Steel;HINDALCO,Hindalco Industries;VEDL,Vedanta;COALINDIA,Coal India;NMDC,NMDC;SAIL,Steel Authority of India;JINDALSTEL,Jindal Steel & Power
Automobiles|MARUTI,Maruti Suzuki India;M&M,Mahindra & Mahindra;TATAMOTORS,Tata Motors;BAJAJ-AUTO,Bajaj Auto;EICHERMOT,Eicher Motors;HEROMOTOCO,Hero MotoCorp;TVSMOTOR,TVS Motor Company;ASHOKLEY,Ashok Leyland;BOSCHLTD,Bosch
FMCG|HINDUNILVR,Hindustan Unilever;ITC,ITC;NESTLEIND,Nestle India;BRITANNIA,Britannia Industries;DABUR,Dabur India;GODREJCP,Godrej Consumer Products;MARICO,Marico;COLPAL,Colgate-Palmolive (India)
Power & Utilities|NTPC,NTPC;POWERGRID,Power Grid Corporation of India;TATAPOWER,Tata Power Company;ADANIGREEN,Adani Green Energy;ADANIPOWER,Adani Power;TORNTPOWER,Torrent Power;NHPC,NHPC;JSWENERGY,JSW Energy
Cement & Construction|ULTRACEMCO,UltraTech Cement;GRASIM,Grasim Industries;AMBUJACEM,Ambuja Cements;SHREECEM,Shree Cement;ACC,ACC;LT,Larsen & Toubro;DLF,DLF;GODREJPROP,Godrej Properties;ADANIPORTS,Adani Ports and SEZ
Consumer & Telecom|BHARTIARTL,Bharti Airtel;IDEA,Vodafone Idea;INDUSTOWER,Indus Towers;TITAN,Titan Company;ASIANPAINT,Asian Paints;TRENT,Trent;DMART,Avenue Supermarts;ZOMATO,Zomato
"""

_SECTOR_PROFILE = {  # base opm %, capex % of sales, base debt/equity, growth mu
    "IT": (24, 3, 0.05, 0.11), "Banking": (30, 2, 7.5, 0.13), "Financial Services": (32, 2, 4.0, 0.15),
    "Oil & Gas": (14, 9, 0.6, 0.07), "Pharma": (23, 6, 0.2, 0.10), "Metals & Mining": (20, 10, 0.9, 0.08),
    "Automobiles": (13, 6, 0.4, 0.10), "FMCG": (22, 3, 0.1, 0.09), "Power & Utilities": (35, 14, 1.8, 0.09),
    "Cement & Construction": (17, 9, 0.7, 0.10), "Consumer & Telecom": (22, 7, 0.8, 0.12),
}
_FINANCIAL = {"Banking", "Financial Services"}
_YEARS = list(range(2016, 2026))
_SHORT_HISTORY = {"ZOMATO": 2}          # fewer than 3 years -> must be skipped by tearsheet batch
_FORCE_DISTRESS = {"IDEA", "ADANIPOWER", "TATAPOWER", "VEDL"}
_FORCE_LOSS = {"IDEA", "SAIL"}
_PATTERN_BY_SIGNS = {
    (1, -1, -1): "Reinvestor", (1, -1, 1): "Aggressive Expander", (1, 1, -1): "Asset Monetizer",
    (1, 1, 1): "Cash Accumulator", (-1, -1, 1): "Capital Raiser", (-1, -1, -1): "Cash Burner",
    (-1, 1, 1): "Distress Signal", (-1, 1, -1): "Asset Liquidator",
}


def company_master() -> pd.DataFrame:
    rows, cid = [], 1
    for line in _RAW.strip().splitlines():
        sector, items = line.split("|")
        for item in items.split(";"):
            ticker, name = item.split(",", 1)
            rows.append({"company_id": cid, "company_name": name, "ticker": ticker, "sector": sector,
                         "is_financial": sector in _FINANCIAL})
            cid += 1
    return pd.DataFrame(rows)


def _sign(v: float) -> int:
    return 1 if v >= 0 else -1


def generate_dataset(seed: int = 42) -> Dict[str, pd.DataFrame]:
    companies = company_master()
    pl, bs, cf, ratios, cagr_rows, ca_rows, analysis_rows = [], [], [], [], [], [], []
    for _, comp in companies.iterrows():
        rng = np.random.default_rng(seed + int(comp["company_id"]))
        opm0, capex_pct, de0, mu = _SECTOR_PROFILE[comp["sector"]]
        fin = bool(comp["is_financial"])
        n_years = _SHORT_HISTORY.get(comp["ticker"], len(_YEARS))
        years = _YEARS[-n_years:]
        sales = float(np.exp(rng.normal(9.4, 1.0)))
        opm = opm0 + rng.normal(0, 3)
        drift = rng.normal(0, 0.9) if rng.random() > 0.2 else -abs(rng.normal(1.2, 0.4))  # some margin erosion
        equity = sales * rng.uniform(0.35, 0.8)
        debt_free = (not fin) and rng.random() < 0.22
        debt = 0.0 if debt_free else equity * max(0.05, de0 * rng.uniform(0.5, 1.6))
        debt_trend = rng.choice([-0.12, -0.04, 0.0, 0.06, 0.18])
        total_assets_prev, prev_debt = None, None
        history = {k: [] for k in ("sales", "np", "eps")}
        for idx, year in enumerate(years):
            g = mu + rng.normal(0, 0.06)
            if comp["ticker"] in {"IDEA", "SAIL"} and idx >= len(years) - 3:
                g = -abs(rng.normal(0.08, 0.03))
            sales *= 1 + g
            opm = float(np.clip(opm + drift + rng.normal(0, 0.8), 3, 60))
            op_profit = sales * opm / 100
            dep = sales * 0.03
            if not debt_free:
                debt = max(0.0, debt * (1 + debt_trend + rng.normal(0, 0.05)))
            interest = debt * (0.09 if not fin else 0.05)
            other_inc = sales * 0.012
            pbt = op_profit - dep - interest + other_inc
            if comp["ticker"] in _FORCE_LOSS and idx == len(years) - 1:
                pbt = -abs(pbt) * 0.4 - sales * 0.02
            net_profit = pbt * 0.75 if pbt > 0 else pbt
            shares = max(sales / 120, 1)
            eps = net_profit / shares
            payout = float(np.clip(rng.normal(32, 20), 0, 60)) if net_profit > 0 else 0.0
            if comp["ticker"] in {"VEDL", "ITC"} and idx == len(years) - 1:
                payout = 118.0
            equity += net_profit * (1 - payout / 100)
            equity = max(equity, sales * 0.05)
            other_liab = sales * 0.28 * (1 + rng.normal(0, 0.04))
            total_assets = equity + debt + other_liab

            cfo = net_profit * float(np.clip(rng.normal(1.05, 0.35), -0.2, 2.2)) + dep
            cfi = -(sales * capex_pct / 100 * float(rng.uniform(0.6, 1.4)))
            dividends = max(net_profit, 0) * payout / 100
            d_debt = 0.0 if prev_debt is None else debt - prev_debt
            cff = d_debt - dividends - interest
            if rng.random() < 0.10:                     # asset sale year -> positive investing flow
                cfi = abs(cfi) * 0.5
            if rng.random() < 0.18:                     # fresh funding raised
                cff = abs(cff) + sales * 0.04
            if comp["ticker"] in _FORCE_DISTRESS and idx == len(years) - 1:
                cfo = -abs(cfo) * 0.6 - sales * 0.01
                cff = abs(cff) + sales * 0.03
                if comp["ticker"] in {"IDEA", "VEDL"}:
                    cfi = abs(cfi) * 0.4
            net_cf = cfo + cfi + cff
            fcf = cfo + cfi
            cash = sales * 0.08

            pl.append(dict(company_id=comp["company_id"], year=year, sales=round(sales, 1),
                           operating_profit=round(op_profit, 1), opm_pct=round(opm, 2),
                           net_profit=round(net_profit, 1), eps=round(eps, 2),
                           dividend_payout_pct=round(payout, 1), interest=round(interest, 1)))
            bs.append(dict(company_id=comp["company_id"], year=year,
                           equity_capital=round(equity * 0.05, 1), reserves=round(equity * 0.95, 1),
                           borrowings=round(debt, 1), other_liabilities=round(other_liab, 1),
                           total_assets=round(total_assets, 1)))
            cf.append(dict(company_id=comp["company_id"], year=year, operating_activity=round(cfo, 1),
                           investing_activity=round(cfi, 1), financing_activity=round(cff, 1),
                           net_cash_flow=round(net_cf, 1)))
            roe = net_profit / equity * 100
            roce = (pbt + interest) / (equity + debt) * 100
            icr = (op_profit - dep) / interest if interest > 0 else np.nan
            ratios.append(dict(company_id=comp["company_id"], year=year, roe_pct=round(roe, 2),
                               roce_pct=round(roce, 2), de_ratio=round(debt / equity, 3),
                               icr=round(icr, 2) if not np.isnan(icr) else np.nan,
                               dividend_yield_pct=round(float(np.clip(rng.normal(1.6, 1.1), 0, 5)), 2),
                               fcf=round(fcf, 1), ebitda=round(op_profit, 1),
                               net_debt=round(debt - cash, 1)))
            ca_rows.append(dict(company_id=comp["company_id"], year=year,
                                pattern=_PATTERN_BY_SIGNS[(_sign(cfo), _sign(cfi), _sign(cff))]))
            history["sales"].append(sales); history["np"].append(net_profit); history["eps"].append(eps)
            prev_debt = debt

        # ---- analysis.xlsx text + Ratio Engine CAGR -------------------------------- #
        def _cg(vals, n):
            if len(vals) <= n or vals[-n - 1] <= 0 or vals[-1] <= 0:
                return np.nan
            return ((vals[-1] / vals[-n - 1]) ** (1 / n) - 1) * 100

        texts = {}
        engine = {"compounded_sales_growth": history["sales"], "compounded_profit_growth": history["np"]}
        for field in settings.TARGET_TEXT_FIELDS:
            parts = []
            for n in (10, 5, 3):
                if field in engine:
                    true_v = _cg(engine[field], n)
                else:
                    true_v = rng.normal(14, 9) if field == "stock_price_cagr" else float(np.mean([r["roe_pct"] for r in ratios[-min(n, len(years)):] if r["company_id"] == comp["company_id"]]))
                if np.isnan(true_v):
                    continue
                engine_v = round(float(true_v), 1)
                stated = engine_v + (rng.normal(0, 1.2) if rng.random() > 0.08 else rng.choice([-9, 9]))
                parts.append(f"{n} Years: {stated:.1f}%")
                cagr_rows.append(dict(company_id=comp["company_id"], metric_type=field, period_years=n, value_pct=engine_v))
            if rng.random() < 0.06:
                parts.append("TTM: 12%")          # deliberately unparseable -> parse_failures.csv
            texts[field] = "\n".join(parts) if parts and rng.random() > 0.02 else ("N/A" if rng.random() < 0.5 else "\n".join(parts))
        analysis_rows.append({"company_id": comp["company_id"], **texts})

    return {
        "companies": companies, "profit_loss": pd.DataFrame(pl), "balance_sheet": pd.DataFrame(bs),
        "cash_flow": pd.DataFrame(cf), "ratios": pd.DataFrame(ratios),
        "ratio_engine_cagr": pd.DataFrame(cagr_rows), "capital_allocation": pd.DataFrame(ca_rows),
        "analysis": pd.DataFrame(analysis_rows),
    }


def write_dataset(frames: Dict[str, pd.DataFrame]) -> None:
    settings.ensure_directories()
    for name, df in frames.items():
        if name == "analysis":
            df.to_excel(settings.ANALYSIS_XLSX, index=False)
        else:
            df.to_csv(settings.INPUT_FILES[name], index=False)
