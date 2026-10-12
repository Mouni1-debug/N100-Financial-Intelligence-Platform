"""
Valuation Module
Sprint 4 - Day 26: FCF yield, P/E analysis, and overvaluation flags

Computes:
- FCF yield (FCF / Market Cap)
- Sector median P/E
- P/E vs sector median
- Overvaluation flags (Caution, Discount, Fair)
"""

import pandas as pd
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class ValuationEngine:
    """
    Valuation analysis engine for 92 companies.
    
    Day 26 Implementation:
    - FCF Yield = (FCF / Market Cap) × 100
    - Sector Median P/E = median(P/E for all companies in sector, latest year)
    - P/E vs Sector Median = ((P/E - Sector Median) / Sector Median) × 100
    - Caution Flag: P/E > Sector Median × 1.5
    - Discount Flag: P/E < Sector Median × 0.7
    - Fair Flag: Otherwise
    """
    
    def __init__(self, db_path: str = "db/nifty100.db"):
        """Initialize valuation engine."""
        self.db_path = db_path
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("ValuationEngine initialized")
    
    def load_company_data(self) -> pd.DataFrame:
        """
        Load company financial and valuation data.
        
        Returns:
            DataFrame with company_id, company_name, sector, pe_ratio, 
            pb_ratio, ev_ebitda, fcf, market_cap
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                c.company_id,
                c.company_name,
                c.broad_sector,
                c.nse_ticker,
                fr.pe_ratio,
                fr.pb_ratio,
                fr.ev_ebitda,
                fr.free_cash_flow_cr,
                c.market_cap_cr,
                pl.eps
            FROM companies c
            JOIN financial_ratios fr ON c.company_id = fr.company_id
            JOIN profit_loss pl ON c.company_id = pl.company_id
            WHERE fr.fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
            AND pl.fiscal_year = (SELECT MAX(fiscal_year) FROM profit_loss)
            ORDER BY c.company_id
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"Loaded financial data for {len(df)} companies")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load company data: {e}")
            raise
    
    def calculate_fcf_yield(self, fcf: float, market_cap: float) -> Optional[float]:
        """
        Calculate FCF yield percentage.
        
        Formula: FCF Yield (%) = (FCF / Market Cap) × 100
        
        Args:
            fcf: Free cash flow in Crores
            market_cap: Market cap in Crores
            
        Returns:
            FCF yield as percentage, or None if calculation not possible
        """
        if pd.isna(fcf) or pd.isna(market_cap) or market_cap <= 0:
            return None
        
        return (fcf / market_cap) * 100
    
    def calculate_sector_median_pe(self, df: pd.DataFrame, sector: str) -> float:
        """
        Calculate median P/E for a sector.
        
        Args:
            df: DataFrame with all companies
            sector: Broad sector name
            
        Returns:
            Median P/E for sector
        """
        sector_pe = df[df['broad_sector'] == sector]['pe_ratio'].dropna()
        
        if len(sector_pe) == 0:
            return np.nan
        
        return sector_pe.median()
    
    def calculate_pe_vs_sector_median(self, pe: float, sector_median_pe: float) -> Optional[float]:
        """
        Calculate % difference between company P/E and sector median P/E.
        
        Formula: P/E vs Sector Median (%) = ((P/E - Sector Median) / Sector Median) × 100
        
        Args:
            pe: Company P/E ratio
            sector_median_pe: Sector median P/E
            
        Returns:
            % difference, or None if not calculable
        """
        if pd.isna(pe) or pd.isna(sector_median_pe) or sector_median_pe <= 0:
            return None
        
        return ((pe - sector_median_pe) / sector_median_pe) * 100
    
    def determine_valuation_flag(self, pe: float, sector_median_pe: float) -> Tuple[str, str]:
        """
        Determine overvaluation/discount flag based on P/E vs sector median.
        
        Rules:
        - Caution: P/E > Sector Median × 1.5 (overvalued)
        - Discount: P/E < Sector Median × 0.7 (undervalued)
        - Fair: Otherwise
        
        Args:
            pe: Company P/E ratio
            sector_median_pe: Sector median P/E
            
        Returns:
            Tuple of (flag, reason)
        """
        if pd.isna(pe) or pd.isna(sector_median_pe):
            return ('N/A', 'Insufficient data')
        
        if pe > sector_median_pe * 1.5:
            reason = f"P/E {pe:.1f}x > Sector Median {sector_median_pe:.1f}x × 1.5"
            return ('Caution', reason)
        
        elif pe < sector_median_pe * 0.7:
            reason = f"P/E {pe:.1f}x < Sector Median {sector_median_pe:.1f}x × 0.7"
            return ('Discount', reason)
        
        else:
            return ('Fair', f"P/E {pe:.1f}x near sector median {sector_median_pe:.1f}x")
    
    def compute_valuation_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all valuation metrics for all companies.
        
        Args:
            df: DataFrame with company financial data
            
        Returns:
            DataFrame with valuation metrics
        """
        results = []
        
        # Get all unique sectors
        sectors = df['broad_sector'].unique()
        sector_medians = {sector: self.calculate_sector_median_pe(df, sector) 
                         for sector in sectors}
        
        logger.info(f"Sector median P/E ratios computed for {len(sectors)} sectors")
        
        for idx, row in df.iterrows():
            company_id = row['company_id']
            company_name = row['company_name']
            sector = row['broad_sector']
            pe = row['pe_ratio']
            pb = row['pb_ratio']
            ev_ebitda = row['ev_ebitda']
            fcf = row['free_cash_flow_cr']
            market_cap = row['market_cap_cr']
            
            # Calculate FCF yield
            fcf_yield = self.calculate_fcf_yield(fcf, market_cap)
            
            # Get sector median P/E
            sector_median_pe = sector_medians.get(sector, np.nan)
            
            # Calculate P/E vs sector median
            pe_vs_sector = self.calculate_pe_vs_sector_median(pe, sector_median_pe)
            
            # Determine valuation flag
            flag, reason = self.determine_valuation_flag(pe, sector_median_pe)
            
            results.append({
                'company_id': company_id,
                'company_name': company_name,
                'sector': sector,
                'pe_ratio': pe,
                'pb_ratio': pb,
                'ev_ebitda': ev_ebitda,
                'fcf_yield_pct': fcf_yield,
                'sector_median_pe': sector_median_pe,
                'pe_vs_sector_median_pct': pe_vs_sector,
                'valuation_flag': flag,
                'flag_reason': reason
            })
        
        result_df = pd.DataFrame(results)
        logger.info(f"Computed valuation metrics for {len(result_df)} companies")
        
        return result_df
    
    def export_valuation_summary(self, valuation_df: pd.DataFrame) -> str:
        """
        Export valuation summary to Excel.
        
        Creates output/valuation_summary.xlsx with 92 rows and all columns.
        
        Args:
            valuation_df: DataFrame with valuation metrics
            
        Returns:
            Path to exported file
        """
        try:
            output_path = self.output_dir / "valuation_summary.xlsx"
            
            # Select columns for export
            export_df = valuation_df[[
                'company_id', 'company_name', 'sector',
                'pe_ratio', 'pb_ratio', 'ev_ebitda',
                'fcf_yield_pct', 'sector_median_pe',
                'pe_vs_sector_median_pct', 'valuation_flag'
            ]].copy()
            
            # Rename for better readability
            export_df.columns = [
                'Company ID', 'Company Name', 'Sector',
                'P/E Ratio', 'P/B Ratio', 'EV/EBITDA',
                'FCF Yield (%)', '5yr Median P/E',
                'P/E vs Sector Median (%)', 'Valuation Flag'
            ]
            
            # Round numeric columns
            numeric_cols = ['P/E Ratio', 'P/B Ratio', 'EV/EBITDA', 'FCF Yield (%)',
                           '5yr Median P/E', 'P/E vs Sector Median (%)']
            for col in numeric_cols:
                if col in export_df.columns:
                    export_df[col] = export_df[col].round(2)
            
            # Write to Excel
            export_df.to_excel(output_path, index=False, sheet_name='Valuation')
            
            logger.info(f"Valuation summary exported to: {output_path}")
            logger.info(f"File contains {len(export_df)} companies")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export valuation summary: {e}")
            raise
    
    def export_valuation_flags(self, valuation_df: pd.DataFrame) -> str:
        """
        Export only Caution and Discount flagged companies to CSV.
        
        Creates output/valuation_flags.csv with flagged companies only.
        
        Args:
            valuation_df: DataFrame with valuation metrics
            
        Returns:
            Path to exported file
        """
        try:
            # Filter for flagged companies
            flagged = valuation_df[
                valuation_df['valuation_flag'].isin(['Caution', 'Discount'])
            ].copy()
            
            output_path = self.output_dir / "valuation_flags.csv"
            
            # Select columns for export
            export_df = flagged[[
                'company_id', 'company_name', 'sector',
                'pe_ratio', 'sector_median_pe',
                'pe_vs_sector_median_pct', 'valuation_flag', 'flag_reason'
            ]].copy()
            
            # Rename for readability
            export_df.columns = [
                'Company ID', 'Company Name', 'Sector',
                'Current P/E', 'Sector Median P/E', 'P/E vs Sector (%)',
                'Flag', 'Reason'
            ]
            
            # Round numeric columns
            numeric_cols = ['Current P/E', 'Sector Median P/E', 'P/E vs Sector (%)']
            for col in numeric_cols:
                if col in export_df.columns:
                    export_df[col] = export_df[col].round(2)
            
            # Sort by P/E vs Sector descending (most overvalued first)
            export_df = export_df.sort_values('P/E vs Sector (%)', ascending=False)
            
            # Write to CSV
            export_df.to_csv(output_path, index=False)
            
            caution_count = len(flagged[flagged['valuation_flag'] == 'Caution'])
            discount_count = len(flagged[flagged['valuation_flag'] == 'Discount'])
            
            logger.info(f"Valuation flags exported to: {output_path}")
            logger.info(f"Caution: {caution_count} companies, Discount: {discount_count} companies")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export valuation flags: {e}")
            raise
    
    def run(self) -> Tuple[str, str]:
        """
        Execute full valuation analysis.
        
        Returns:
            Tuple of (valuation_summary_path, valuation_flags_path)
        """
        logger.info("Starting valuation analysis...")
        
        # Load data
        df = self.load_company_data()
        
        # Compute metrics
        valuation_df = self.compute_valuation_metrics(df)
        
        # Export results
        summary_path = self.export_valuation_summary(valuation_df)
        flags_path = self.export_valuation_flags(valuation_df)
        
        # Summary statistics
        caution_count = len(valuation_df[valuation_df['valuation_flag'] == 'Caution'])
        discount_count = len(valuation_df[valuation_df['valuation_flag'] == 'Discount'])
        fair_count = len(valuation_df[valuation_df['valuation_flag'] == 'Fair'])
        
        logger.info("\n" + "="*70)
        logger.info("VALUATION ANALYSIS COMPLETE")
        logger.info("="*70)
        logger.info(f"Caution (Overvalued): {caution_count} companies")
        logger.info(f"Discount (Undervalued): {discount_count} companies")
        logger.info(f"Fair Value: {fair_count} companies")
        logger.info("="*70)
        
        return summary_path, flags_path


def main():
    """Main entry point for valuation analysis."""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    engine = ValuationEngine()
    summary_path, flags_path = engine.run()
    
    print(f"\n✅ Valuation Summary: {summary_path}")
    print(f"✅ Valuation Flags: {flags_path}")


if __name__ == "__main__":
    main()
