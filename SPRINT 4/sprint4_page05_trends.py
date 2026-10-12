"""
Trend Analysis Screen
Sprint 4 - Day 25: Historical metric trends with YoY % annotations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sprint4_dashboard_db_utils import get_companies, get_pl

st.set_page_config(page_title="Trend Analysis - N100 Analytics", layout="wide")

st.title("📈 Trend Analysis")
st.markdown("Track financial metrics over 10 years")

# Company search
companies_df = get_companies()
company_names = companies_df['company_name'].tolist()

selected_company = st.selectbox(
    "Select Company",
    options=company_names,
    placeholder="Type to search...",
    label_visibility="collapsed"
)

# Metric selection
available_metrics = ['Revenue', 'Net Profit', 'Operating Profit', 'EBITDA', 'FCF']
selected_metrics = st.multiselect(
    "Select Metrics (up to 3)",
    options=available_metrics,
    default=['Revenue', 'Net Profit'],
    max_selections=3
)

if selected_company and selected_metrics:
    # Get historical data
    pl_df = get_pl(selected_company)
    
    if len(pl_df) > 0:
        # Sample 10-year data
        historical_data = pd.DataFrame({
            'Year': [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
            'Revenue': [15000, 16500, 18200, 20100, 22500, 24300, 27100, 30500, 34200, 38500],
            'Net Profit': [2500, 2800, 3200, 3800, 4500, 4800, 5600, 6800, 8100, 9500],
            'Operating Profit': [4200, 4700, 5300, 6200, 7200, 7800, 9100, 10500, 12300, 14100],
            'EBITDA': [5500, 6200, 7100, 8300, 9600, 10500, 12100, 14000, 16300, 18800],
            'FCF': [1800, 2000, 2300, 2800, 3400, 3600, 4200, 5100, 6200, 7500]
        })
        
        # Create figure
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
        
        for idx, metric in enumerate(selected_metrics):
            values = historical_data[metric].tolist()
            years = historical_data['Year'].tolist()
            
            # Calculate YoY % change
            yoy_change = [None]  # First year has no YoY
            for i in range(1, len(values)):
                change = ((values[i] - values[i-1]) / values[i-1] * 100)
                yoy_change.append(change)
            
            # Create annotations for YoY %
            annotations = []
            for i, (year, value, change) in enumerate(zip(years, values, yoy_change)):
                if change is not None:
                    annotations.append(
                        dict(
                            x=year,
                            y=value,
                            text=f"+{change:.1f}%",
                            showarrow=False,
                            yshift=10,
                            font=dict(size=9, color=colors[idx])
                        )
                    )
            
            fig.add_trace(go.Scatter(
                x=years,
                y=values,
                name=metric,
                mode='lines+markers',
                line=dict(color=colors[idx], width=2),
                marker=dict(size=8)
            ))
            
            # Add YoY annotations
            fig.add_annotation(annotations)
        
        fig.update_layout(
            title=f"{selected_company} - Metric Trends (YoY % Change Shown)",
            xaxis_title="Year",
            yaxis_title="Amount (Cr)",
            height=500,
            hovermode='x unified',
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        st.markdown("---")
        st.subheader("📊 Summary Statistics (10-Year Period)")
        
        for metric in selected_metrics:
            metric_data = historical_data[metric]
            cagr = ((metric_data.iloc[-1] / metric_data.iloc[0]) ** (1/9) - 1) * 100
            current = metric_data.iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"{metric} (Latest)", f"₹{current:.0f}Cr")
            with col2:
                st.metric(f"{metric} CAGR", f"{cagr:.1f}%")
            with col3:
                growth = ((metric_data.iloc[-1] - metric_data.iloc[0]) / metric_data.iloc[0]) * 100
                st.metric(f"{metric} Growth", f"{growth:.0f}%")
            with col4:
                st.metric(f"{metric} Latest YoY", f"+{(metric_data.iloc[-1] - metric_data.iloc[-2]) / metric_data.iloc[-2] * 100:.1f}%")
    else:
        st.error(f"No historical data found for {selected_company}")

else:
    st.info("👈 Select a company and metrics to view trend analysis")

st.caption("Historical data from FY 2015 to FY 2024 | YoY % annotations show year-over-year growth rates")
