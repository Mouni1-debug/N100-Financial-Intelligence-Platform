"""
N100 Financial Intelligence Platform - Streamlit Dashboard
Sprint 4 - Day 22: Main Streamlit Application

Multi-page dashboard with 8 screens for company analysis.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit page configuration
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "N100 Financial Intelligence Platform - Sprint 4 Dashboard"
    }
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    h1 {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    h2 {
        color: #2c3e50;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    
    # Sidebar header
    with st.sidebar:
        st.title("🏠 Nifty 100 Analytics")
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        pages = {
            "🏠 Home": "pages/01_home",
            "👤 Company Profile": "pages/02_profile",
            "🔍 Screener": "pages/03_screener",
            "👥 Peer Comparison": "pages/04_peers",
            "📈 Trend Analysis": "pages/05_trends",
            "🏭 Sector Analysis": "pages/06_sectors",
            "💰 Capital Allocation": "pages/07_capital",
            "📄 Annual Reports": "pages/08_reports"
        }
        
        selected = st.radio(
            "Select Screen",
            options=list(pages.keys()),
            index=0,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Sidebar info
        st.subheader("Dashboard Info")
        st.info("""
        **N100 Financial Intelligence Platform**
        
        • **Companies**: 92 (Nifty 100)
        • **Metrics**: 20+ financial KPIs
        • **Peer Groups**: 11
        • **Data Year**: 2024 (Latest)
        
        **Features**:
        - Real-time screening
        - Peer comparison
        - Valuation analysis
        - Capital allocation tracking
        """)
        
        st.markdown("---")
        st.caption("Sprint 4 - Dashboard & Valuation Module | Day 22-28")
    
    # Route to selected page
    if selected == "🏠 Home":
        st.switch_page("pages/01_home.py")
    elif selected == "👤 Company Profile":
        st.switch_page("pages/02_profile.py")
    elif selected == "🔍 Screener":
        st.switch_page("pages/03_screener.py")
    elif selected == "👥 Peer Comparison":
        st.switch_page("pages/04_peers.py")
    elif selected == "📈 Trend Analysis":
        st.switch_page("pages/05_trends.py")
    elif selected == "🏭 Sector Analysis":
        st.switch_page("pages/06_sectors.py")
    elif selected == "💰 Capital Allocation":
        st.switch_page("pages/07_capital.py")
    elif selected == "📄 Annual Reports":
        st.switch_page("pages/08_reports.py")
    
    # Default home view if no page selected
    st.title("🏠 Nifty 100 Financial Intelligence Platform")
    st.write("""
    Welcome to the N100 Financial Intelligence Platform Dashboard!
    
    This comprehensive analytics tool provides:
    
    ✅ **Real-time Financial Screening** - Filter companies by 15+ metrics
    ✅ **Peer Comparison Analysis** - Compare with industry peers
    ✅ **Trend Analysis** - Track metrics over 10 years
    ✅ **Sector Analysis** - Bubble charts and sector benchmarks
    ✅ **Capital Allocation Tracking** - Understand company strategies
    ✅ **Valuation Assessment** - FCF yield and P/E analysis
    ✅ **Annual Reports** - Easy access to BSE-filed documents
    
    **Get Started**: Select a screen from the sidebar to explore!
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Companies", 92, "Nifty 100")
    with col2:
        st.metric("Sectors", 11, "Coverage")
    with col3:
        st.metric("KPI Metrics", 20, "Tracked")
    with col4:
        st.metric("Data Years", 10, "Historical")


if __name__ == "__main__":
    main()
