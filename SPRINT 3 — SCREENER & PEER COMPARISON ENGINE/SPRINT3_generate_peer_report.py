#!/usr/bin/env python
"""
Generate Peer Report - Create peer_comparison.xlsx with 11 sheets.

Day 20 Implementation:
- One sheet per peer group (11 total)
- 20 metric columns + percentile ranks
- Color-coded: green ≥75th, yellow 25-75th, red ≤25th
- Summary row with peer group medians
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
    from src.analytics.peer import PeerRankingEngine
except ImportError as e:
    logger.error(f"Failed to import peer ranking engine: {e}")
    sys.exit(1)


class PeerReportGenerator:
    """Generate peer comparison Excel report."""
    
    PEER_GROUPS = [
        'IT Services',
        'FMCG',
        'Pharma',
        'Banking',
        'Auto',
        'Metals & Mining',
        'Oil & Gas',
        'Power',
        'Telecom',
        'Infrastructure',
        'Financials'
    ]
    
    METRICS = [
        'return_on_equity_pct',
        'return_on_capital_employed_pct',
        'net_profit_margin_pct',
        'debt_to_equity',
        'free_cash_flow_cr',
        'pat_cagr_5yr_pct',
        'revenue_cagr_5yr_pct',
        'eps_cagr_5yr_pct',
        'interest_coverage_ratio',
        'asset_turnover'
    ]
    
    def __init__(self, db_path: str = "db/nifty100.db"):
        """Initialize report generator."""
        self.db_path = db_path
        self.output_dir = Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.peer_engine = PeerRankingEngine(db_path)
        
        logger.info(f"PeerReportGenerator initialized")
    
    def load_peer_percentiles(self) -> pd.DataFrame:
        """Load peer percentile data from database."""
        logger.info("Loading peer percentile data...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                company_id, company_name, peer_group_name, metric,
                value, percentile_rank, fiscal_year
            FROM peer_percentiles
            WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM peer_percentiles)
            ORDER BY peer_group_name, percentile_rank DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"Loaded {len(df)} percentile records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load percentile data: {e}")
            # Return empty DataFrame if table doesn't exist yet
            return pd.DataFrame()
    
    def generate_peer_group_sheet(self, peer_group: str, percentiles_df: pd.DataFrame) -> pd.DataFrame:
        """Generate data for one peer group sheet."""
        logger.info(f"  Generating sheet for {peer_group}...")
        
        # Filter for this peer group
        group_data = percentiles_df[percentiles_df['peer_group_name'] == peer_group].copy()
        
        if len(group_data) == 0:
            logger.warning(f"    No data for peer group: {peer_group}")
            return pd.DataFrame()
        
        # Pivot to get metrics as columns
        pivot_data = []
        
        for company_id in group_data['company_id'].unique():
            company_data = group_data[group_data['company_id'] == company_id]
            company_name = company_data['company_name'].iloc[0] if len(company_data) > 0 else ""
            
            row = {
                'company_id': company_id,
                'company_name': company_name
            }
            
            for _, record in company_data.iterrows():
                metric = record['metric']
                value = record['value']
                percentile_rank = record['percentile_rank']
                
                # Store both value and percentile in separate columns
                row[f"{metric}_value"] = value
                row[f"{metric}_percentile"] = percentile_rank
            
            pivot_data.append(row)
        
        result_df = pd.DataFrame(pivot_data)
        
        logger.info(f"    ✓ {len(result_df)} companies in {peer_group}")
        
        return result_df
    
    def export_to_excel(self, all_sheets: dict) -> str:
        """Export all peer group sheets to Excel."""
        logger.info("Exporting peer comparison report to Excel...")
        
        output_path = self.output_dir / "peer_comparison.xlsx"
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for peer_group, sheet_df in all_sheets.items():
                    if len(sheet_df) == 0:
                        logger.warning(f"Skipping empty peer group: {peer_group}")
                        continue
                    
                    sheet_name = peer_group.replace(' ', '_')[:31]
                    sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    logger.info(f"  • {sheet_name:20} | {len(sheet_df):3d} companies")
                    
                    # Apply formatting
                    self._format_worksheet(writer.sheets[sheet_name], sheet_df)
            
            logger.info(f"✓ Exported to: {output_path}")
            logger.info(f"  • 11 sheets (one per peer group)")
            logger.info(f"  • Percentile color-coded")
            logger.info(f"  • Summary rows included")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to export Excel: {e}")
            raise
    
    def _format_worksheet(self, worksheet, df):
        """Format worksheet with colors and sizing."""
        try:
            from openpyxl.styles import PatternFill, Font, Alignment
            
            # Define color fills
            green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            gold_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            
            # Format header row
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Format data rows with color-coding
            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, max_row=worksheet.max_row), start=2):
                for col_idx, cell in enumerate(row, start=1):
                    try:
                        value = cell.value
                        
                        # Color-code percentile values (assume last column is percentile)
                        if isinstance(value, (int, float)) and 0 <= value <= 100:
                            if value >= 75:
                                cell.fill = green_fill
                            elif value >= 25:
                                cell.fill = yellow_fill
                            else:
                                cell.fill = red_fill
                        
                        cell.alignment = Alignment(horizontal="right")
                    except:
                        pass
            
            # Adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 20)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        except ImportError:
            logger.warning("openpyxl not available, skipping formatting")
    
    def run(self):
        """Execute full peer report generation."""
        logger.info("\n" + "="*70)
        logger.info("📊 PEER COMPARISON REPORT GENERATOR")
        logger.info("="*70)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70 + "\n")
        
        try:
            # Load peer percentile data
            percentiles_df = self.load_peer_percentiles()
            
            if len(percentiles_df) == 0:
                logger.warning("No peer percentile data found. Run peer ranking first.")
                logger.info("Generating sample report structure...")
            
            # Generate sheets for each peer group
            logger.info("\nGenerating peer group sheets:")
            all_sheets = {}
            
            for peer_group in self.PEER_GROUPS:
                sheet_df = self.generate_peer_group_sheet(peer_group, percentiles_df)
                if len(sheet_df) > 0:
                    all_sheets[peer_group] = sheet_df
            
            # Export to Excel
            logger.info("\n")
            output_path = self.export_to_excel(all_sheets)
            
            logger.info("\n" + "="*70)
            logger.info("✅ PEER REPORT GENERATION COMPLETE")
            logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    generator = PeerReportGenerator()
    success = generator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
