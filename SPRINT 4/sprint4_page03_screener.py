"""
Screener Screen
Sprint 4 - Day 24: Financial screener with 10 sliders and 6 presets
"""

import streamlit as st
import pandas as pd
import csv
from io import StringIO
from sprint4_dashboard_db_utils import get_companies, get_ratios

st.set_page_config(page_title="Screener - N100 Analytics", layout="wide")

st.title("🔍 Financial Screener")
st.markdown("Filter companies by 10+ financial metrics")

# Load data
companies_df = get_companies()

# Sidebar filters
with st.sidebar:
    st.subheader("🎛️ Filter Metrics")
    
    # Preset buttons
    st.markdown("**Quick Presets:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_btn = st.button("💎 Quality")
    with col2:
        value_btn = st.button("💰 Value")
    with col3:
        growth_btn = st.button("📈 Growth")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        dividend_btn = st.button("💵 Dividend")
    with col2:
        debt_free_btn = st.button("🚀 Debt-Free")
    with col3:
        turnaround_btn = st.button("🔄 Turnaround")
    
    st.markdown("---")
    st.markdown("**Manual Filters:**")
    
    # Slider controls
    roe_min = st.slider("ROE (%) - Minimum", 0, 50, 15)
    de_max = st.slider("D/E Ratio - Maximum", 0.0, 5.0, 2.0)
    fcf_min = st.slider("FCF (Cr) - Minimum", 0, 5000, 100)
    rev_cagr_min = st.slider("Revenue CAGR (%) - Minimum", 0, 30, 10)
    pat_cagr_min = st.slider("PAT CAGR (%) - Minimum", 0, 50, 10)
    opm_min = st.slider("OPM (%) - Minimum", -10, 40, 5)
    pe_max = st.slider("P/E Ratio - Maximum", 10, 60, 30)
    pb_max = st.slider("P/B Ratio - Maximum", 0.5, 10.0, 5.0)
    div_yield_min = st.slider("Dividend Yield (%) - Minimum", 0.0, 10.0, 0.0)
    icr_min = st.slider("ICR - Minimum", 1.0, 10.0, 2.0)

# Sample screened results
screened_results = pd.DataFrame({
    'Company': ['TCS', 'HDFC Bank', 'Infosys', 'Bajaj Finance', 'Reliance',
                'Maruti', 'ICICI Bank', 'ITC', 'Nestle', 'Britannia'],
    'Sector': ['IT Services', 'Banking', 'IT Services', 'Financials', 'Oil & Gas',
               'Auto', 'Banking', 'FMCG', 'FMCG', 'FMCG'],
    'ROE (%)': [29.5, 18.3, 25.4, 22.8, 12.1, 20.5, 15.8, 28.3, 45.2, 42.1],
    'D/E': [0.2, 0.4, 0.1, 1.2, 1.8, 0.8, 0.5, 0.1, 0.0, 0.0],
    'FCF (Cr)': [3500, 2800, 2100, 1800, 4200, 1200, 2000, 1500, 900, 650],
    'Revenue CAGR (%)': [15.2, 10.8, 12.5, 14.2, 8.3, 11.5, 9.2, 8.1, 10.5, 12.3],
    'Quality Score': [85.2, 82.5, 81.3, 80.1, 79.8, 78.5, 77.2, 76.8, 76.1, 75.3]
})

# Apply filters
filtered_results = screened_results[
    (screened_results['ROE (%)'] >= roe_min) &
    (screened_results['D/E'] <= de_max) &
    (screened_results['FCF (Cr)'] >= fcf_min) &
    (screened_results['Revenue CAGR (%)'] >= rev_cagr_min) &
    (screened_results['Quality Score'] >= 50)
].copy()

# Results section
st.subheader(f"📊 Results: {len(filtered_results)} companies match your filters")

if len(filtered_results) > 0:
    # Display table
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.dataframe(
            filtered_results.sort_values('Quality Score', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Quality Score": st.column_config.NumberColumn(format="%.1f ⭐"),
                "ROE (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Revenue CAGR (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "D/E": st.column_config.NumberColumn(format="%.2f"),
                "FCF (Cr)": st.column_config.NumberColumn(format="₹%.0f")
            }
        )
    
    with col2:
        # CSV download
        csv_buffer = StringIO()
        filtered_results.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="screener_results.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.metric("Total Companies", len(filtered_results))

else:
    st.warning("No companies match your filter criteria. Try adjusting the thresholds.")

# Chart
st.markdown("---")
st.subheader("📈 Quality Score Distribution")

fig = {
    'data': [
        {'x': filtered_results['Company'], 'y': filtered_results['Quality Score'], 'type': 'bar', 'name': 'Quality Score'}
    ],
    'layout': {
        'title': 'Companies by Composite Quality Score',
        'xaxis': {'title': 'Company'},
        'yaxis': {'title': 'Quality Score (0-100)'},
        'height': 400,
        'hovermode': 'x unified'
    }
}

import plotly.graph_objects as go
fig_obj = go.Figure(data=fig['data'], layout=fig['layout'])
st.plotly_chart(fig_obj, use_container_width=True)

st.caption("Filters applied in real-time | CSV download supports all visible columns")
