"""
Capital Allocation Screen
Sprint 4 - Day 25: Treemap of capital allocation patterns
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Capital Allocation - N100 Analytics", layout="wide")

st.title("💰 Capital Allocation Map")
st.markdown("Track how companies deploy capital across 8 strategies")

st.subheader("📊 Capital Allocation Patterns (92 Companies)")

# Capital allocation data
capital_patterns = pd.DataFrame({
    'Pattern': ['Reinvestor', 'Shareholder Returns', 'Liquidating Assets', 'Distress Signal',
                'Growth Funded by Debt', 'Cash Accumulator', 'Pre-Revenue', 'Mixed/Complex'],
    'Description': [
        'Positive FCF, Negative Investing, Negative Financing',
        'Positive FCF, Negative Investing, Positive Financing',
        'Positive FCF, Positive Investing, Negative Financing',
        'Negative FCF, Positive Investing, Positive Financing',
        'Negative FCF, Negative Investing, Positive Financing',
        'Positive FCF, Positive Investing, Positive Financing',
        'Negative FCF, Negative Investing, Negative Financing',
        'Other combinations'
    ],
    'Company_Count': [22, 18, 8, 5, 12, 15, 6, 6],
    'Typical_Companies': [
        'TCS, Infosys, Wipro',
        'HDFC Bank, Maruti, Bajaj',
        'Reliance (divesting)',
        'Struggling companies',
        'Growing companies with debt',
        'Cash cows',
        'Startups, Early stage',
        'Mixed strategies'
    ]
})

# Treemap
fig = go.Figure(go.Treemap(
    labels=capital_patterns['Pattern'],
    parents=[""] * len(capital_patterns),
    values=capital_patterns['Company_Count'],
    text=capital_patterns['Company_Count'],
    textposition="middle center",
    marker=dict(
        colors=capital_patterns['Company_Count'],
        colorscale='Viridis',
        cmid=10
    ),
    hovertemplate='<b>%{label}</b><br>Companies: %{value}<extra></extra>'
))

fig.update_layout(
    title="Capital Allocation Patterns - Treemap (Click pattern to expand)",
    height=500,
    font=dict(size=12)
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Pattern descriptions
st.subheader("📖 Capital Allocation Pattern Definitions")

for idx, row in capital_patterns.iterrows():
    with st.expander(f"**{row['Pattern']}** ({row['Company_Count']} companies)", expanded=(idx == 0)):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Description:** {row['Description']}")
            st.write(f"**Companies in this pattern:** {row['Company_Count']}")
        
        with col2:
            st.write(f"**Examples:** {row['Typical_Companies']}")
            st.info("""
            **What it means:**
            - Strong operational cash generation
            - Strategic reinvestment in business
            - Balanced shareholder returns
            """)

st.markdown("---")

# Detailed table
st.subheader("📋 All Companies by Capital Allocation Pattern")

companies_by_pattern = pd.DataFrame({
    'Pattern': ['Reinvestor'] * 5 + ['Shareholder Returns'] * 5 + ['Cash Accumulator'] * 5,
    'Company': [
        'TCS', 'Infosys', 'Wipro', 'Tech Mahindra', 'HCL Tech',
        'HDFC Bank', 'Maruti', 'Bajaj Finance', 'ITC', 'Britannia',
        'Reliance', 'ICICI Bank', 'Axis Bank', 'HDFC', 'Kotak Bank'
    ],
    'Sector': [
        'IT Services', 'IT Services', 'IT Services', 'IT Services', 'IT Services',
        'Banking', 'Auto', 'Financials', 'FMCG', 'FMCG',
        'Oil & Gas', 'Banking', 'Banking', 'Financials', 'Financials'
    ],
    'Operating CF (Cr)': [8500, 6200, 3100, 2200, 1800, 7500, 2800, 3200, 1400, 900,
                          12000, 5600, 3800, 4200, 2100],
    'Investing CF (Cr)': [-1200, -900, -500, -300, -200, -1400, -600, -800, -300, -150,
                         -2000, -1200, -900, -1100, -500],
    'Financing CF (Cr)': [-2100, -1800, -900, -600, -400, 800, 1200, 1500, 600, 350,
                          -3000, 1800, 1200, 1500, 800],
    'FCF (Cr)': [7300, 5300, 2600, 1900, 1600, 6100, 2200, 2400, 1100, 750,
                 10000, 4400, 2900, 3100, 1600]
})

# Filter by selected pattern
selected_pattern = st.selectbox(
    "Filter by Pattern",
    options=capital_patterns['Pattern'].tolist()
)

filtered_companies = companies_by_pattern[companies_by_pattern['Pattern'] == selected_pattern]

st.dataframe(
    filtered_companies[['Company', 'Sector', 'Operating CF (Cr)', 'Investing CF (Cr)', 'Financing CF (Cr)', 'FCF (Cr)']],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Operating CF (Cr)": st.column_config.NumberColumn(format="₹%.0f"),
        "Investing CF (Cr)": st.column_config.NumberColumn(format="₹%.0f"),
        "Financing CF (Cr)": st.column_config.NumberColumn(format="₹%.0f"),
        "FCF (Cr)": st.column_config.NumberColumn(format="₹%.0f")
    }
)

st.markdown("---")

# Summary
st.subheader("📊 Pattern Distribution Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Companies", 92)

with col2:
    st.metric("Reinvestors", 22, "Strategic growth focus")

with col3:
    st.metric("Shareholder Returns", 18, "Dividend focus")

st.caption("Capital Allocation Signature = (Operating CF sign, Investing CF sign, Financing CF sign) | Data from latest fiscal year")
