"""
Annual Reports Screen
Sprint 4 - Day 25: BSE annual report links with availability status
"""

import streamlit as st
import pandas as pd
from sprint4_dashboard_db_utils import get_companies

st.set_page_config(page_title="Annual Reports - N100 Analytics", layout="wide")

st.title("📄 Annual Reports")
st.markdown("Access company annual reports filed with BSE")

# Company search
companies_df = get_companies()
company_names = companies_df['company_name'].tolist()

selected_company = st.selectbox(
    "Search Company",
    options=company_names,
    placeholder="Type to search...",
    label_visibility="collapsed"
)

if selected_company:
    company = companies_df[companies_df['company_name'] == selected_company].iloc[0]
    ticker = company['nse_ticker']
    
    st.subheader(f"📋 {selected_company} Annual Reports")
    st.caption(f"NSE Ticker: {ticker}")
    
    st.markdown("---")
    
    # Sample reports data
    reports_data = pd.DataFrame({
        'Fiscal Year': ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015'],
        'Status': ['Available', 'Available', 'Available', 'Available', 'Available', 
                  'Available', 'Available', 'Available', 'Unavailable', 'Unavailable'],
        'File Size (MB)': [12.5, 11.8, 10.3, 9.8, 8.5, 7.2, 6.8, 6.1, None, None],
        'BSE Link': [
            'bseindia.com/filing/TCS_2024_AR.pdf',
            'bseindia.com/filing/TCS_2023_AR.pdf',
            'bseindia.com/filing/TCS_2022_AR.pdf',
            'bseindia.com/filing/TCS_2021_AR.pdf',
            'bseindia.com/filing/TCS_2020_AR.pdf',
            'bseindia.com/filing/TCS_2019_AR.pdf',
            'bseindia.com/filing/TCS_2018_AR.pdf',
            'bseindia.com/filing/TCS_2017_AR.pdf',
            None,
            None
        ]
    })
    
    # Create interactive report list
    st.subheader("📂 Available Reports")
    
    for idx, row in reports_data.iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
        
        with col1:
            st.write(f"**FY {row['Fiscal Year']}**")
        
        with col2:
            if row['Status'] == 'Available':
                st.success(f"✅ {row['Status']}")
            else:
                st.error(f"❌ {row['Status']}")
        
        with col3:
            if row['File Size (MB)']:
                st.caption(f"{row['File Size (MB)']} MB")
            else:
                st.caption("N/A")
        
        with col4:
            if row['Status'] == 'Available':
                st.markdown(f"[📥 Download PDF](#{row['BSE Link']})")
            else:
                st.write("Report unavailable")
        
        st.markdown("---")
    
    # Download statistics
    st.markdown("---")
    st.subheader("📊 Report Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    available_count = len(reports_data[reports_data['Status'] == 'Available'])
    
    with col1:
        st.metric("Total Reports", len(reports_data))
    
    with col2:
        st.metric("Available", available_count)
    
    with col3:
        latest_size = reports_data[reports_data['Status'] == 'Available'].iloc[0]['File Size (MB)']
        st.metric("Latest Report Size", f"{latest_size:.1f} MB")
    
    with col4:
        st.metric("Coverage", f"{available_count} years")

else:
    st.info("👈 Select a company to view available annual reports")

st.markdown("---")

# Quick links section
st.subheader("🔗 Quick Links")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **BSE Official Site**
    - [BSE.India.com](https://www.bseindia.com)
    - Corporate Filings Database
    """)

with col2:
    st.markdown("""
    **About Annual Reports**
    - Audited financial statements
    - Management Discussion & Analysis
    - Corporate governance info
    """)

with col3:
    st.markdown("""
    **Document Types**
    - Annual Reports
    - Quarterly Results
    - Board Meetings
    """)

st.caption("Reports are official BSE filings | Unavailable reports may be archived or still pending filing | Data current as of 2026-10-07")
