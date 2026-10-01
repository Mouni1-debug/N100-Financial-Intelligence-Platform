#!/usr/bin/env python
"""
Generate Radar Charts - Create 92 radar chart visualizations.

Day 19 Implementation:
- 8-axis radar charts for each company
- Company polygon + peer group average dashed overlay
- 150 DPI PNG export
- reports/radar_charts/{company_id}_radar.png
"""

import pandas as pd
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.analytics.visualization import RadarChartGenerator
except ImportError as e:
    logger.error(f"Failed to import visualization module: {e}")
    sys.exit(1)


class RadarChartRunner:
    """Runner for generating radar charts."""
    
    def __init__(self, db_path: str = "db/nifty100.db"):
        """Initialize radar chart runner."""
        self.db_path = db_path
        self.output_dir = Path("reports/radar_charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.generator = RadarChartGenerator(str(self.output_dir))
        
        logger.info(f"RadarChartRunner initialized")
        logger.info(f"Output directory: {self.output_dir}")
    
    def load_financial_data(self) -> pd.DataFrame:
        """Load financial data from database."""
        logger.info("Loading financial data for radar charts...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                company_id, company_name, broad_sector,
                return_on_equity_pct, return_on_capital_employed_pct,
                net_profit_margin_pct, debt_to_equity,
                free_cash_flow_cr, pat_cagr_5yr_pct,
                revenue_cagr_5yr_pct, composite_quality_score
            FROM financial_ratios
            WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
            ORDER BY company_id
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"Loaded {len(df)} companies")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def load_peer_mapping(self) -> pd.DataFrame:
        """Load peer group mapping."""
        logger.info("Loading peer group mapping...")
        
        try:
            # Try to load from Excel
            peer_mapping_path = Path("config/peer_groups.xlsx")
            
            if peer_mapping_path.exists():
                peer_mapping = pd.read_excel(peer_mapping_path)
                logger.info(f"Loaded peer mapping for {len(peer_mapping)} companies")
                return peer_mapping
            else:
                # If no mapping file, create from sector
                logger.warning("peer_groups.xlsx not found, using broad_sector as mapping")
                # This will be handled in generator
                return pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"Could not load peer mapping: {e}")
            return pd.DataFrame()
    
    def run(self):
        """Execute full radar chart generation."""
        logger.info("\n" + "="*70)
        logger.info("📊 RADAR CHART GENERATOR")
        logger.info("="*70)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70 + "\n")
        
        try:
            # Load data
            df = self.load_financial_data()
            peer_mapping = self.load_peer_mapping()
            
            # Generate radar charts
            logger.info("Generating radar charts...")
            logger.info("─" * 70)
            
            # Simple approach: generate chart for each company
            charts_generated = 0
            
            for idx, row in df.iterrows():
                company_id = row['company_id']
                company_name = row['company_name']
                
                try:
                    # Prepare values for this company
                    company_values = {
                        'return_on_equity_pct': row.get('return_on_equity_pct', 0),
                        'return_on_capital_employed_pct': row.get('return_on_capital_employed_pct', 0),
                        'net_profit_margin_pct': row.get('net_profit_margin_pct', 0),
                        'debt_to_equity_inverted': 100 / (1 + row.get('debt_to_equity', 0)) if row.get('debt_to_equity', 0) >= 0 else 0,
                        'fcf_score': max(0, min(100, row.get('free_cash_flow_cr', 0) / 50)),  # Normalized
                        'pat_cagr_5yr_pct': row.get('pat_cagr_5yr_pct', 0),
                        'revenue_cagr_5yr_pct': row.get('revenue_cagr_5yr_pct', 0),
                        'composite_quality_score': row.get('composite_quality_score', 50)
                    }
                    
                    # Get peer group
                    peer_group = None
                    if len(peer_mapping) > 0:
                        peer_rows = peer_mapping[peer_mapping['company_id'] == company_id]
                        if len(peer_rows) > 0:
                            peer_group = peer_rows.iloc[0]['peer_group_name']
                    
                    # Calculate peer average
                    if peer_group and len(peer_mapping) > 0:
                        peer_companies = peer_mapping[peer_mapping['peer_group_name'] == peer_group]['company_id'].tolist()
                        peer_data = df[df['company_id'].isin(peer_companies)]
                    else:
                        peer_data = df
                    
                    peer_avg = {
                        'return_on_equity_pct': peer_data['return_on_equity_pct'].mean(),
                        'return_on_capital_employed_pct': peer_data['return_on_capital_employed_pct'].mean(),
                        'net_profit_margin_pct': peer_data['net_profit_margin_pct'].mean(),
                        'debt_to_equity_inverted': (100 / (1 + peer_data['debt_to_equity'])).mean(),
                        'fcf_score': (peer_data['free_cash_flow_cr'].mean() / 50).clip(0, 100),
                        'pat_cagr_5yr_pct': peer_data['pat_cagr_5yr_pct'].mean(),
                        'revenue_cagr_5yr_pct': peer_data['revenue_cagr_5yr_pct'].mean(),
                        'composite_quality_score': peer_data['composite_quality_score'].mean()
                    }
                    
                    # Generate chart
                    path = self.generator.generate_radar_chart(
                        company_id=company_id,
                        company_name=company_name,
                        company_values=pd.Series(company_values),
                        peer_avg_values=pd.Series(peer_avg),
                        peer_group=peer_group
                    )
                    
                    charts_generated += 1
                    
                    if (idx + 1) % 10 == 0:
                        logger.info(f"  ✓ Generated {charts_generated:2d} charts...")
                
                except Exception as e:
                    logger.warning(f"  Failed to generate chart for {company_name}: {e}")
                    continue
            
            logger.info("─" * 70)
            logger.info(f"\n✓ Generated {charts_generated} radar charts")
            logger.info(f"  Location: {self.output_dir}/")
            logger.info(f"  Filename format: {{company_id}}_radar.png")
            
            logger.info("\n" + "="*70)
            logger.info("✅ RADAR CHART GENERATION COMPLETE")
            logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Radar chart generation failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    runner = RadarChartRunner()
    success = runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
