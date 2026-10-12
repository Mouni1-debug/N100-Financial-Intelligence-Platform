"""
Database Utilities for Dashboard
Sprint 4 - Day 22: Cached data loader functions

All functions use @st.cache_data(ttl=600) for performance.
"""

import streamlit as st
import pandas as pd
import sqlite3
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class DashboardDataLoader:
    """Cached data loader for dashboard."""
    
    DB_PATH = "db/nifty100.db"
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_companies() -> pd.DataFrame:
        """
        Get all 92 companies with basic info.
        
        Returns:
            DataFrame: company_id, company_name, sector, broad_sector, nse_ticker
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = """
            SELECT 
                company_id, company_name, sector, broad_sector, 
                nse_ticker, market_cap_cr, dividend_yield_pct
            FROM companies
            ORDER BY company_name
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            logger.info(f"Loaded {len(df)} companies")
            return df
        except Exception as e:
            logger.error(f"Failed to load companies: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_ratios(ticker: str, year: Optional[int] = None) -> pd.DataFrame:
        """
        Get financial ratios for a company.
        
        Args:
            ticker: Company NSE ticker
            year: Optional fiscal year (default: latest)
            
        Returns:
            DataFrame with financial ratios
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            
            if year:
                query = f"""
                SELECT * FROM financial_ratios
                WHERE nse_ticker = '{ticker}' AND fiscal_year = {year}
                """
            else:
                query = f"""
                SELECT * FROM financial_ratios
                WHERE nse_ticker = '{ticker}'
                AND fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
                """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to load ratios for {ticker}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_pl(ticker: str) -> pd.DataFrame:
        """
        Get P&L statement for company (10 years).
        
        Args:
            ticker: Company NSE ticker
            
        Returns:
            DataFrame: revenue, net_profit, operating_profit, etc.
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = f"""
            SELECT 
                fiscal_year, revenue_cr, net_profit_cr, 
                operating_profit_cr, ebitda_cr, eps
            FROM profit_loss
            WHERE nse_ticker = '{ticker}'
            ORDER BY fiscal_year DESC
            LIMIT 10
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df.sort_values('fiscal_year')
        except Exception as e:
            logger.error(f"Failed to load P&L for {ticker}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_bs(ticker: str) -> pd.DataFrame:
        """
        Get Balance Sheet data (10 years).
        
        Args:
            ticker: Company NSE ticker
            
        Returns:
            DataFrame: assets, liabilities, equity, etc.
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = f"""
            SELECT 
                fiscal_year, total_assets_cr, total_liabilities_cr,
                equity_cr, current_assets_cr, current_liabilities_cr
            FROM balance_sheet
            WHERE nse_ticker = '{ticker}'
            ORDER BY fiscal_year DESC
            LIMIT 10
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df.sort_values('fiscal_year')
        except Exception as e:
            logger.error(f"Failed to load BS for {ticker}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_cf(ticker: str) -> pd.DataFrame:
        """
        Get Cash Flow statement (10 years).
        
        Args:
            ticker: Company NSE ticker
            
        Returns:
            DataFrame: operating_cf, investing_cf, financing_cf, free_cf
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = f"""
            SELECT 
                fiscal_year, operating_cf_cr, investing_cf_cr,
                financing_cf_cr, free_cash_flow_cr
            FROM cash_flow
            WHERE nse_ticker = '{ticker}'
            ORDER BY fiscal_year DESC
            LIMIT 10
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df.sort_values('fiscal_year')
        except Exception as e:
            logger.error(f"Failed to load CF for {ticker}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_sectors() -> List[str]:
        """
        Get list of all sectors.
        
        Returns:
            List of sector names
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = "SELECT DISTINCT broad_sector FROM companies ORDER BY broad_sector"
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df['broad_sector'].tolist()
        except Exception as e:
            logger.error(f"Failed to load sectors: {e}")
            return []
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_peers(group_name: str) -> pd.DataFrame:
        """
        Get all companies in a peer group.
        
        Args:
            group_name: Peer group name (e.g., 'IT Services')
            
        Returns:
            DataFrame: All companies in peer group with key metrics
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = f"""
            SELECT 
                c.company_id, c.company_name, c.broad_sector,
                fr.return_on_equity_pct, fr.debt_to_equity,
                fr.operating_profit_margin_pct, fr.net_profit_cr,
                fr.composite_quality_score
            FROM companies c
            JOIN financial_ratios fr ON c.company_id = fr.company_id
            WHERE c.peer_group = '{group_name}'
            AND fr.fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
            ORDER BY c.company_name
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to load peers for {group_name}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_valuation(ticker: str) -> Dict:
        """
        Get valuation metrics for a company.
        
        Args:
            ticker: Company NSE ticker
            
        Returns:
            Dict with valuation metrics (P/E, P/B, FCF yield, flags)
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = f"""
            SELECT 
                pe_ratio, pb_ratio, ev_ebitda, fcf_yield_pct,
                valuation_flag, overvaluation_reason
            FROM valuation
            WHERE nse_ticker = '{ticker}'
            AND fiscal_year = (SELECT MAX(fiscal_year) FROM valuation)
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) > 0:
                return df.iloc[0].to_dict()
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to load valuation for {ticker}: {e}")
            return {}
    
    @staticmethod
    @st.cache_data(ttl=600)
    def get_sector_stats() -> pd.DataFrame:
        """
        Get sector-level statistics.
        
        Returns:
            DataFrame: Sector metrics (count, median ROE, median P/E, etc.)
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            query = """
            SELECT 
                c.broad_sector,
                COUNT(c.company_id) as company_count,
                AVG(fr.return_on_equity_pct) as avg_roe,
                MEDIAN(fr.pe_ratio) as median_pe,
                AVG(fr.debt_to_equity) as avg_de,
                SUM(fr.market_cap_cr) as total_market_cap
            FROM companies c
            JOIN financial_ratios fr ON c.company_id = fr.company_id
            WHERE fr.fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
            GROUP BY c.broad_sector
            ORDER BY c.broad_sector
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to load sector stats: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=600)
    def search_companies(query: str) -> pd.DataFrame:
        """
        Search companies by name or ticker.
        
        Args:
            query: Search term
            
        Returns:
            DataFrame: Matching companies
        """
        try:
            conn = sqlite3.connect(DashboardDataLoader.DB_PATH)
            sql_query = f"""
            SELECT 
                company_id, company_name, nse_ticker, broad_sector
            FROM companies
            WHERE company_name LIKE '%{query}%'
            OR nse_ticker LIKE '%{query}%'
            ORDER BY company_name
            """
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            return df
        except Exception as e:
            logger.error(f"Failed to search companies: {e}")
            return pd.DataFrame()


# Convenience functions
def get_companies():
    """Get all companies."""
    return DashboardDataLoader.get_companies()


def get_ratios(ticker, year=None):
    """Get ratios for a company."""
    return DashboardDataLoader.get_ratios(ticker, year)


def get_pl(ticker):
    """Get P&L statement."""
    return DashboardDataLoader.get_pl(ticker)


def get_bs(ticker):
    """Get balance sheet."""
    return DashboardDataLoader.get_bs(ticker)


def get_cf(ticker):
    """Get cash flow."""
    return DashboardDataLoader.get_cf(ticker)


def get_sectors():
    """Get all sectors."""
    return DashboardDataLoader.get_sectors()


def get_peers(group_name):
    """Get companies in peer group."""
    return DashboardDataLoader.get_peers(group_name)


def get_valuation(ticker):
    """Get valuation metrics."""
    return DashboardDataLoader.get_valuation(ticker)
