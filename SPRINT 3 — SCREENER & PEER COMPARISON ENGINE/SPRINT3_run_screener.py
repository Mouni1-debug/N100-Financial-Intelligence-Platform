#!/usr/bin/env python
"""
Run Screener - Main execution script for N100 Sprint 3 Screener Engine.

Day 15-17 Implementation:
- Load financial data from database
- Calculate composite quality scores
- Run 6 preset screeners
- Export results to Excel (6 sheets)
"""

import pandas as pd
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import screener components
try:
    from src.screener.engine import ScreenerEngine
    from src.screener.presets import ScreenerPresets
    from src.screener.composite_score import CompositeScoreCalculator
    from src.screener.validators import ScreenerValidator
except ImportError as e:
    logger.error(f"Failed to import screener modules: {e}")
    sys.exit(1)


class ScreenerRunner:
    """Main screener execution runner."""
    
    def __init__(self, db_path: str = "db/nifty100.db", config_path: str = "config/screener_config.yaml"):
        """Initialize screener runner."""
        self.db_path = db_path
        self.config_path = config_path
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ScreenerRunner initialized")
        logger.info(f"Database: {db_path}")
        logger.info(f"Config: {config_path}")
        logger.info(f"Output: {self.output_dir}")
    
    def load_financial_data(self) -> pd.DataFrame:
        """Load financial data from SQLite database."""
        logger.info("Loading financial data from database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                company_id, company_name, broad_sector, sector,
                return_on_equity_pct, return_on_capital_employed_pct,
                net_profit_margin_pct, debt_to_equity,
                free_cash_flow_cr, revenue_cagr_3yr_pct, revenue_cagr_5yr_pct,
                pat_cagr_3yr_pct, pat_cagr_5yr_pct, eps_cagr_5yr_pct,
                operating_profit_margin_pct, pe_ratio, pb_ratio,
                dividend_yield_pct, interest_coverage_ratio, icr_label,
                market_cap_cr, net_profit_cr, sales_cr, asset_turnover,
                fcf_cagr_5yr_pct, cfo_quality_score, dividend_payout_ratio
            FROM financial_ratios
            WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM financial_ratios)
            ORDER BY company_id
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"Loaded {len(df)} companies with {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def validate_input_data(self, df: pd.DataFrame) -> bool:
        """Validate input data."""
        logger.info("Validating input data...")
        
        if not ScreenerValidator.validate_input_dataframe(df):
            logger.error("Input validation failed")
            return False
        
        logger.info("✓ Input validation passed")
        return True
    
    def calculate_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate composite quality scores."""
        logger.info("Calculating composite quality scores...")
        
        import yaml
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        calculator = CompositeScoreCalculator(config)
        
        # Calculate main composite score
        df = calculator.calculate_composite_score(df)
        logger.info(f"Composite scores calculated. Mean: {df['composite_quality_score'].mean():.1f}")
        
        # Calculate sector-relative score
        df = calculator.calculate_sector_relative_score(df)
        logger.info("Sector-relative scores calculated")
        
        return df
    
    def run_all_presets(self, df: pd.DataFrame) -> dict:
        """Run all 6 preset screeners."""
        logger.info("Running 6 preset screeners...")
        
        engine = ScreenerEngine(self.config_path)
        presets = ScreenerPresets(engine)
        
        all_results = presets.run_all_presets(df)
        
        logger.info(f"\n📊 Preset Results:")
        logger.info("═" * 60)
        
        for preset_name, (result_df, metadata) in all_results.items():
            count = len(result_df)
            expected = metadata.get('expected_count', 'N/A')
            logger.info(f"  {metadata['name']:30} | Found: {count:3d} (Expected: {expected})")
        
        logger.info("═" * 60)
        
        return all_results
    
    def export_screener_results(self, all_results: dict) -> str:
        """Export screener results to Excel (6 sheets)."""
        logger.info("Exporting screener results to Excel...")
        
        output_path = self.output_dir / "screener_output.xlsx"
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for preset_name, (result_df, metadata) in all_results.items():
                    sheet_name = metadata['name'].replace(' ', '_')[:31]  # Sheet name limit
                    
                    # Select KPI columns to export
                    kpi_columns = [
                        'company_id', 'company_name', 'broad_sector',
                        'return_on_equity_pct', 'return_on_capital_employed_pct',
                        'net_profit_margin_pct', 'debt_to_equity',
                        'free_cash_flow_cr', 'revenue_cagr_5yr_pct', 'pat_cagr_5yr_pct',
                        'operating_profit_margin_pct', 'pe_ratio', 'pb_ratio',
                        'dividend_yield_pct', 'interest_coverage_ratio',
                        'market_cap_cr', 'net_profit_cr', 'sales_cr', 'asset_turnover',
                        'composite_quality_score'
                    ]
                    
                    # Keep only available columns
                    export_cols = [col for col in kpi_columns if col in result_df.columns]
                    export_df = result_df[export_cols].copy()
                    
                    # Sort by composite score descending
                    export_df = export_df.sort_values('composite_quality_score', ascending=False)
                    
                    # Write to Excel
                    export_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    logger.info(f"  • {sheet_name:25} | {len(export_df):3d} companies")
                    
                    # Format worksheet (if openpyxl available)
                    try:
                        from openpyxl.styles import PatternFill
                        worksheet = writer.sheets[sheet_name]
                        
                        # Header formatting
                        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                        for cell in worksheet[1]:
                            cell.fill = header_fill
                            cell.font = cell.font.copy()
                            cell.font = cell.font.copy()
                            cell.font = cell.font.copy()
                        
                        # Adjust column widths
                        for column in worksheet.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column:
                                try:
                                    if len(str(cell.value)) > max_length:
                                        max_length = len(cell.value)
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 50)
                            worksheet.column_dimensions[column_letter].width = adjusted_width
                    except:
                        pass
            
            logger.info(f"✓ Exported to: {output_path}")
            logger.info(f"  • 6 sheets (one per preset)")
            logger.info(f"  • 20 KPI columns")
            logger.info(f"  • Sorted by composite score (descending)")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            raise
    
    def generate_summary_report(self, all_results: dict):
        """Generate and print summary report."""
        logger.info("\n" + "="*70)
        logger.info("SCREENER EXECUTION SUMMARY")
        logger.info("="*70)
        
        total_companies = 0
        for preset_name, (result_df, metadata) in all_results.items():
            count = len(result_df)
            total_companies += count
            logger.info(f"  {metadata['name']:30} {count:3d} companies")
        
        logger.info("="*70)
        logger.info(f"Total unique companies across presets: {total_companies}")
        logger.info("="*70)
    
    def run(self):
        """Execute full screener pipeline."""
        logger.info("\n" + "="*70)
        logger.info("🚀 N100 SPRINT 3 - SCREENER ENGINE")
        logger.info("="*70)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70 + "\n")
        
        try:
            # Step 1: Load data
            df = self.load_financial_data()
            
            # Step 2: Validate
            if not self.validate_input_data(df):
                logger.error("Validation failed, aborting")
                return False
            
            # Step 3: Calculate scores
            df = self.calculate_composite_scores(df)
            
            # Step 4: Run presets
            all_results = self.run_all_presets(df)
            
            # Step 5: Export results
            self.export_screener_results(all_results)
            
            # Step 6: Summary
            self.generate_summary_report(all_results)
            
            logger.info("\n" + "="*70)
            logger.info("✅ SCREENER EXECUTION COMPLETE")
            logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Screener execution failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    runner = ScreenerRunner()
    success = runner.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
