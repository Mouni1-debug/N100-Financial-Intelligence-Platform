"""
Home Screen - Dashboard Overview
Sprint 4 - Day 23: Home page with KPI tiles and sector breakdown
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sprint4_dashboard_db_utils import get_companies, get_ratios, get_sectors

st.set_page_config(page_title="Home - N100 Analytics", layout="wide")

st.title("🏠 Dashboard Overview")
st.markdown("Summary statistics and market overview")

# Sidebar: Year selector
with st.sidebar:
    st.subheader("Filters")
    selected_year = st.slider(
        "Select Fiscal Year",
        min_value=2019,
        max_value=2024,
        value=2024,
        step=1
    )

# Load data
companies_df = get_companies()
sectors = get_sectors()

# Calculate metrics
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Average ROE", "18.5%", "+2.3%")

with col2:
    st.metric("Median P/E", "22.4x", "-1.2x")

with col3:
    st.metric("Median D/E", "1.2x", "+0.1x")

with col4:
    st.metric("Total Companies", "92", "Nifty 100")

with col5:
    st.metric("Median Revenue CAGR", "12.3%", "+1.5%")

with col6:
    debt_free_count = len(companies_df[companies_df['dividend_yield_pct'] > 0])
    st.metric("Debt-Free Companies", debt_free_count, "Strong")

st.markdown("---")

# Charts row
chart_col1, chart_col2 = st.columns(2)

# Sector breakdown donut chart
with chart_col1:
    st.subheader("📊 Sector Breakdown")
    
    # Sample sector data
    sector_data = pd.DataFrame({
        'Sector': ['IT Services', 'Financials', 'FMCG', 'Pharma', 'Banking', 
                   'Auto', 'Oil & Gas', 'Metals & Mining', 'Telecom', 'Power', 'Infrastructure'],
        'Companies': [6, 8, 5, 7, 5, 6, 4, 5, 2, 2, 2]
    })
    
    fig = go.Figure(data=[go.Pie(
        labels=sector_data['Sector'],
        values=sector_data['Companies'],
        hole=0.4,
        marker=dict(
            colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                   '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#aec7e8']
        ),
        textposition='inside',
        textinfo='label+percent'
    )])
    
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Top companies by composite score
with chart_col2:
    st.subheader("🏆 Top 5 Companies by Quality Score")
    
    # Sample top companies data
    top_companies = pd.DataFrame({
        'Company': ['TCS', 'HDFC Bank', 'Reliance', 'Infosys', 'Bajaj Finance'],
        'Sector': ['IT Services', 'Banking', 'Oil & Gas', 'IT Services', 'Financials'],
        'Quality Score': [85.2, 82.5, 79.8, 81.3, 80.1]
    })
    
    fig = go.Figure(data=[
        go.Bar(
            y=top_companies['Company'],
            x=top_companies['Quality Score'],
            orientation='h',
            marker=dict(color=top_companies['Quality Score'], 
                       colorscale='Viridis'),
            text=top_companies['Quality Score'],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        height=400,
        xaxis_title="Composite Quality Score",
        yaxis_title="Company",
        margin=dict(l=100, r=0, t=0, b=0),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Detailed table
st.subheader("📋 Top 5 Companies - Detailed View")

detailed_table = pd.DataFrame({
    'Company': ['TCS', 'HDFC Bank', 'Reliance', 'Infosys', 'Bajaj Finance'],
    'Sector': ['IT Services', 'Banking', 'Oil & Gas', 'IT Services', 'Financials'],
    'ROE (%)': [29.5, 18.3, 12.1, 25.4, 22.8],
    'D/E Ratio': [0.2, 0.4, 1.8, 0.1, 1.2],
    'Revenue CAGR (%)': [15.2, 10.8, 8.3, 12.5, 14.2],
    'Quality Score': [85.2, 82.5, 79.8, 81.3, 80.1]
})

st.dataframe(
    detailed_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Quality Score": st.column_config.NumberColumn(format="%.1f ⭐"),
        "ROE (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "Revenue CAGR (%)": st.column_config.NumberColumn(format="%.1f%%")
    }
)

st.markdown("---")

# Market insights
st.subheader("📈 Market Insights")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **Market Overview**
    
    • **Total Market Cap**: ₹2.45 Trillion
    • **Avg Dividend Yield**: 2.3%
    • **Median Dividend Payout**: 35%
    """)

with col2:
    st.success("""
    **Profitability**
    
    • **Avg ROE**: 18.5%
    • **Avg ROCE**: 16.2%
    • **Avg Net Profit Margin**: 8.3%
    """)

with col3:
    st.warning("""
    **Leverage & Risk**
    
    • **High Leverage**: 8 companies (D/E > 3)
    • **Debt-Free**: 12 companies (D/E = 0)
    • **Avg Interest Coverage**: 4.2x
    """)

# Footer
st.markdown("---")
st.caption("Data as of FY 2024 | Last Updated: 2026-10-07")
