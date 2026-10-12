"""
Peer Comparison Screen
Sprint 4 - Day 24: Radar chart and peer group analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sprint4_dashboard_db_utils import get_companies, get_peers, get_ratios

st.set_page_config(page_title="Peer Comparison - N100 Analytics", layout="wide")

st.title("👥 Peer Comparison")
st.markdown("Compare company metrics with peer group average")

# Peer groups
peer_groups = [
    'IT Services', 'FMCG', 'Pharma', 'Banking', 'Auto',
    'Metals & Mining', 'Oil & Gas', 'Power', 'Telecom', 'Infrastructure', 'Financials'
]

col1, col2 = st.columns(2)

with col1:
    selected_group = st.selectbox(
        "Select Peer Group",
        options=peer_groups,
        index=0
    )

with col2:
    # Company selection within peer group
    companies_in_group = ['TCS', 'Infosys', 'Wipro', 'Tech Mahindra', 'HCL Tech', 'L&T Infotech']
    selected_company = st.selectbox(
        "Select Company",
        options=companies_in_group,
        index=0
    )

st.markdown("---")

# Radar chart section
st.subheader("📊 Radar Chart - Company vs Peer Group Average")

# Sample radar data
company_metrics = {
    'ROE': 25.4,
    'ROCE': 21.2,
    'NPM': 18.5,
    'D/E (Inverted)': 80,  # Out of 100
    'FCF Score': 75,
    'PAT CAGR': 22.5,
    'Revenue CAGR': 15.3,
    'Composite Score': 81.3
}

peer_avg = {
    'ROE': 18.5,
    'ROCE': 15.8,
    'NPM': 12.3,
    'D/E (Inverted)': 60,
    'FCF Score': 65,
    'PAT CAGR': 14.2,
    'Revenue CAGR': 11.5,
    'Composite Score': 72.1
}

# Normalize to 0-100 scale for visualization
def normalize_metric(value, min_val=0, max_val=100):
    return max(0, min(100, value))

categories = list(company_metrics.keys())
company_values = [normalize_metric(v) for v in company_metrics.values()]
peer_values = [normalize_metric(v) for v in peer_avg.values()]

fig = go.Figure()

fig.add_trace(go.Scatterpolar(
    r=company_values,
    theta=categories,
    fill='toself',
    name=selected_company,
    marker=dict(color='#1f77b4'),
    line=dict(color='#1f77b4', width=2)
))

fig.add_trace(go.Scatterpolar(
    r=peer_values,
    theta=categories,
    fill='toself',
    name=f'{selected_group} Average',
    marker=dict(color='#ff7f0e'),
    line=dict(color='#ff7f0e', width=2, dash='dash')
))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=True,
    height=500,
    font=dict(size=11)
)

col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Legend")
    st.markdown(f"""
    **{selected_company}** (Solid Line)
    - Company metrics (solid polygon)
    
    **{selected_group}** (Dashed Line)
    - Peer group average (dashed overlay)
    
    **Interpretation:**
    - Larger polygon = stronger metrics
    - Close alignment = in line with peers
    - Bulges out = outperforming peers
    """)

st.markdown("---")

# Peer group table
st.subheader(f"📋 {selected_group} - Peer Metrics Comparison")

peer_table = pd.DataFrame({
    'Company': ['TCS', 'Infosys', 'Wipro', 'Tech Mahindra', 'HCL Tech', 'L&T Infotech'],
    'Sector': ['IT Services'] * 6,
    'ROE (%)': [25.4, 22.8, 20.1, 19.5, 18.3, 17.2],
    'ROCE (%)': [21.2, 19.8, 17.5, 16.8, 15.4, 14.9],
    'Net Profit Margin (%)': [18.5, 16.2, 14.8, 13.9, 12.5, 11.8],
    'D/E Ratio': [0.2, 0.15, 0.25, 0.3, 0.35, 0.28],
    'FCF (Cr)': [3500, 2100, 1200, 850, 620, 380],
    'Quality Score': [85.2, 81.3, 76.5, 73.2, 70.1, 68.5],
    'Percentile Rank': ['95th', '85th', '72nd', '61st', '48th', '38th']
})

# Highlight benchmark company (highest quality score)
highlighted_table = peer_table.copy()

st.dataframe(
    highlighted_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Quality Score": st.column_config.NumberColumn(format="%.1f ⭐"),
        "ROE (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "ROCE (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "Net Profit Margin (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "D/E Ratio": st.column_config.NumberColumn(format="%.2f"),
        "FCF (Cr)": st.column_config.NumberColumn(format="₹%.0f")
    }
)

# Summary stats
st.markdown("---")
st.subheader("📊 Peer Group Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Peer Count", 6)

with col2:
    st.metric("Median ROE", "20.1%")

with col3:
    st.metric("Median D/E", "0.27x")

with col4:
    st.metric("Median Quality", "74.9")

st.caption("Peer percentile ranks: Company compared to all peers in group | Benchmark: Highest quality score")
