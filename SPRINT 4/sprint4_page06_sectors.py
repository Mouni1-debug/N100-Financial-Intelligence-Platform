"""
Sector Analysis Screen
Sprint 4 - Day 25: Bubble chart and sector benchmarks
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sprint4_dashboard_db_utils import get_sectors

st.set_page_config(page_title="Sector Analysis - N100 Analytics", layout="wide")

st.title("🏭 Sector Analysis")
st.markdown("Analyze sector composition and benchmarks")

# Sector selection
sectors = [
    'IT Services', 'FMCG', 'Pharma', 'Banking', 'Auto',
    'Metals & Mining', 'Oil & Gas', 'Power', 'Telecom', 'Infrastructure', 'Financials'
]

selected_sector = st.selectbox(
    "Select Sector",
    options=sectors,
    index=0
)

st.markdown("---")

# Bubble chart - Revenue vs ROE vs Market Cap
st.subheader("📊 Sector Bubble Chart (Revenue vs ROE vs Market Cap)")

sector_data = pd.DataFrame({
    'Company': ['TCS', 'Infosys', 'Wipro', 'Tech Mahindra', 'HCL Tech', 'L&T Infotech'],
    'Sector': ['IT Services'] * 6,
    'Sub-Sector': ['IT Services - Software'] * 6,
    'Revenue': [270000, 180000, 95000, 65000, 52000, 38000],
    'ROE': [25.4, 22.8, 20.1, 19.5, 18.3, 17.2],
    'Market_Cap': [1450000, 820000, 380000, 210000, 125000, 85000],
    'Quality_Score': [85.2, 81.3, 76.5, 73.2, 70.1, 68.5]
})

fig = go.Figure()

# Bubble colors by sub-sector
sub_sectors = sector_data['Sub-Sector'].unique()
colors = px.colors.qualitative.Plotly

for i, sub_sector in enumerate(sub_sectors):
    sub_sector_data = sector_data[sector_data['Sub-Sector'] == sub_sector]
    
    fig.add_trace(go.Scatter(
        x=sub_sector_data['Revenue'],
        y=sub_sector_data['ROE'],
        mode='markers',
        name=sub_sector,
        marker=dict(
            size=sub_sector_data['Market_Cap'] / 10000,
            color=colors[i % len(colors)],
            opacity=0.6,
            line=dict(width=1, color='white')
        ),
        text=sub_sector_data['Company'],
        hovertemplate='<b>%{text}</b><br>Revenue: ₹%{x:.0f}Cr<br>ROE: %{y:.1f}%<extra></extra>'
    ))

fig.update_layout(
    title=f"{selected_sector} - Company Position Map",
    xaxis_title="Revenue (Cr) →",
    yaxis_title="ROE (%) →",
    height=500,
    hovermode='closest',
    legend=dict(x=0.01, y=0.99)
)

st.plotly_chart(fig, use_container_width=True)

st.caption("Bubble size represents Market Cap | Color represents sub-sector")

st.markdown("---")

# Sector median KPI chart
st.subheader("📈 Sector Median Benchmarks")

sector_benchmarks = pd.DataFrame({
    'Metric': ['ROE (%)', 'ROCE (%)', 'Net Margin (%)', 'D/E Ratio', 'Revenue CAGR (%)'],
    'IT Services': [23.5, 20.1, 16.2, 0.22, 15.3],
    'FMCG': [18.2, 15.8, 12.5, 0.15, 8.1],
    'Pharma': [21.3, 18.5, 14.8, 0.28, 10.5],
    'Banking': [14.5, 12.2, 8.3, 1.25, 9.2],
    'Auto': [16.8, 14.1, 6.2, 0.85, 7.3]
})

# Display as grouped bar chart
metrics = sector_benchmarks['Metric'].tolist()
it_services = sector_benchmarks['IT Services'].tolist()
fmcg = sector_benchmarks['FMCG'].tolist()
pharma = sector_benchmarks['Pharma'].tolist()
banking = sector_benchmarks['Banking'].tolist()
auto = sector_benchmarks['Auto'].tolist()

fig = go.Figure(data=[
    go.Bar(name='IT Services', x=metrics, y=it_services, marker=dict(color='#1f77b4')),
    go.Bar(name='FMCG', x=metrics, y=fmcg, marker=dict(color='#ff7f0e')),
    go.Bar(name='Pharma', x=metrics, y=pharma, marker=dict(color='#2ca02c')),
    go.Bar(name='Banking', x=metrics, y=banking, marker=dict(color='#d62728')),
    go.Bar(name='Auto', x=metrics, y=auto, marker=dict(color='#9467bd'))
])

fig.update_layout(
    title="Sector Median KPI Comparison",
    barmode='group',
    xaxis_title="KPI",
    yaxis_title="Value",
    height=400,
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Sector composition
st.subheader(f"📋 {selected_sector} - Company Breakdown")

sector_companies = pd.DataFrame({
    'Company': ['TCS', 'Infosys', 'Wipro', 'Tech Mahindra', 'HCL Tech', 'L&T Infotech'],
    'Market Cap (Cr)': [1450000, 820000, 380000, 210000, 125000, 85000],
    'Revenue (Cr)': [270000, 180000, 95000, 65000, 52000, 38000],
    'ROE (%)': [25.4, 22.8, 20.1, 19.5, 18.3, 17.2],
    'D/E': [0.20, 0.15, 0.25, 0.30, 0.35, 0.28],
    'Quality Score': [85.2, 81.3, 76.5, 73.2, 70.1, 68.5]
})

st.dataframe(
    sector_companies,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Quality Score": st.column_config.NumberColumn(format="%.1f ⭐"),
        "ROE (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "Market Cap (Cr)": st.column_config.NumberColumn(format="₹%.0f"),
        "Revenue (Cr)": st.column_config.NumberColumn(format="₹%.0f"),
        "D/E": st.column_config.NumberColumn(format="%.2f")
    }
)

# Summary metrics
st.markdown("---")
st.subheader(f"📊 {selected_sector} Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Companies", 6)

with col2:
    st.metric("Total Market Cap", "₹3.07T")

with col3:
    st.metric("Median ROE", "21.2%")

with col4:
    st.metric("Avg Quality Score", "75.8")

st.caption("Bubble chart: X-axis = Revenue, Y-axis = ROE, Bubble size = Market Cap | Data current as of FY 2024")
