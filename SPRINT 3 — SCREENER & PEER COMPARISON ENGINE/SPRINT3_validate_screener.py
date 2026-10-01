#!/usr/bin/env python
"""
Validate Screener - Data quality validation and checks.

Day 21 Implementation:
- Validate screener outputs
- Check database constraints
- Verify file exports
- Quality assurance checks
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


class ScreenerValidator:
    """Validate screener outputs and data quality."""
    
    def __init__(self, db_path: str = "db/nifty100.db"):
        """Initialize validator."""
        self.db_path = db_path
        self.output_dir = Path("data/output")
        self.charts_dir = Path("reports/radar_charts")
        
        logger.info(f"ScreenerValidator initialized")
    
    def check_database(self) -> bool:
        """Check database integrity."""
        logger.info("\n[1/5] Checking Database Integrity...")
        logger.info("─" * 60)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check financial_ratios table
            cursor.execute("SELECT COUNT(*) FROM financial_ratios")
            ratio_count = cursor.fetchone()[0]
            logger.info(f"  ✓ financial_ratios: {ratio_count} rows")
            
            if ratio_count == 0:
                logger.warning("  ⚠ WARNING: No data in financial_ratios table")
            
            # Check peer_percentiles table
            try:
                cursor.execute("SELECT COUNT(*) FROM peer_percentiles")
                percentile_count = cursor.fetchone()[0]
                logger.info(f"  ✓ peer_percentiles: {percentile_count} rows")
                
                if percentile_count > 0:
                    # Check percentile distribution
                    cursor.execute("""
                        SELECT COUNT(DISTINCT peer_group_name) 
                        FROM peer_percentiles
                    """)
                    group_count = cursor.fetchone()[0]
                    logger.info(f"  ✓ Peer groups: {group_count}")
            except sqlite3.OperationalError:
                logger.warning("  ⚠ peer_percentiles table not found (run peer ranking first)")
            
            conn.close()
            logger.info("  ✓ Database checks passed")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Database check failed: {e}")
            return False
    
    def check_excel_exports(self) -> bool:
        """Check Excel file exports."""
        logger.info("\n[2/5] Checking Excel Exports...")
        logger.info("─" * 60)
        
        all_ok = True
        
        # Check screener_output.xlsx
        screener_file = self.output_dir / "screener_output.xlsx"
        if screener_file.exists():
            try:
                df = pd.read_excel(screener_file, sheet_name=0)
                logger.info(f"  ✓ screener_output.xlsx ({len(df)} rows)")
                
                # Check for required columns
                required_cols = ['company_id', 'company_name', 'composite_quality_score']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    logger.warning(f"    ⚠ Missing columns: {missing_cols}")
                    all_ok = False
            except Exception as e:
                logger.error(f"  ✗ screener_output.xlsx: {e}")
                all_ok = False
        else:
            logger.warning("  ⚠ screener_output.xlsx not found")
        
        # Check peer_comparison.xlsx
        peer_file = self.output_dir / "peer_comparison.xlsx"
        if peer_file.exists():
            try:
                # Get sheet names
                xls = pd.ExcelFile(peer_file)
                sheet_count = len(xls.sheet_names)
                logger.info(f"  ✓ peer_comparison.xlsx ({sheet_count} sheets)")
                
                if sheet_count < 11:
                    logger.warning(f"    ⚠ Expected 11 sheets, found {sheet_count}")
                    all_ok = False
            except Exception as e:
                logger.error(f"  ✗ peer_comparison.xlsx: {e}")
                all_ok = False
        else:
            logger.warning("  ⚠ peer_comparison.xlsx not found")
        
        if all_ok:
            logger.info("  ✓ Excel export checks passed")
        
        return all_ok
    
    def check_radar_charts(self) -> bool:
        """Check radar chart PNG files."""
        logger.info("\n[3/5] Checking Radar Charts...")
        logger.info("─" * 60)
        
        if not self.charts_dir.exists():
            logger.warning(f"  ⚠ Radar charts directory not found: {self.charts_dir}")
            return False
        
        png_files = list(self.charts_dir.glob("*.png"))
        logger.info(f"  ✓ Found {len(png_files)} PNG files")
        
        if len(png_files) < 92:
            logger.warning(f"  ⚠ Expected 92 charts, found {len(png_files)}")
            return False
        
        if len(png_files) == 92:
            logger.info("  ✓ All 92 radar charts present")
            return True
        
        return len(png_files) > 0
    
    def check_composite_scores(self) -> bool:
        """Check composite quality scores."""
        logger.info("\n[4/5] Checking Composite Scores...")
        logger.info("─" * 60)
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
            SELECT 
                composite_quality_score,
                COUNT(*) as count
            FROM financial_ratios
            GROUP BY ROUND(composite_quality_score, 0)
            ORDER BY composite_quality_score
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) == 0:
                logger.warning("  ⚠ No composite scores found")
                return False
            
            # Check range
            min_score = df['composite_quality_score'].min()
            max_score = df['composite_quality_score'].max()
            mean_score = df['composite_quality_score'].mean()
            
            logger.info(f"  ✓ Score range: {min_score:.1f} - {max_score:.1f}")
            logger.info(f"  ✓ Mean score: {mean_score:.1f}")
            
            # Check distribution
            if 0 <= min_score and max_score <= 100:
                logger.info("  ✓ Scores within 0-100 range")
                return True
            else:
                logger.warning("  ⚠ Scores outside 0-100 range")
                return False
                
        except Exception as e:
            logger.error(f"  ✗ Composite score check failed: {e}")
            return False
    
    def check_preset_results(self) -> bool:
        """Verify preset screener results."""
        logger.info("\n[5/5] Checking Preset Screener Results...")
        logger.info("─" * 60)
        
        screener_file = self.output_dir / "screener_output.xlsx"
        
        if not screener_file.exists():
            logger.warning("  ⚠ screener_output.xlsx not found")
            return False
        
        try:
            xls = pd.ExcelFile(screener_file)
            presets = xls.sheet_names
            
            logger.info(f"  ✓ Found {len(presets)} preset sheets:")
            
            expected_presets = [
                'Quality_Compounder',
                'Value_Pick',
                'Growth_Accelerator',
                'Dividend_Champion',
                'Debt-Free_Blue_Chip',
                'Turnaround_Watch'
            ]
            
            all_ok = True
            for sheet in presets:
                df = pd.read_excel(screener_file, sheet_name=sheet)
                count = len(df)
                
                logger.info(f"    • {sheet:30} | {count:3d} companies")
                
                # Check expected ranges (rough estimate)
                sheet_clean = sheet.replace('_', ' ')
                if 'Quality' in sheet_clean and (count < 5 or count > 50):
                    logger.warning(f"      ⚠ Unexpected count for {sheet_clean}")
                    all_ok = False
            
            if all_ok:
                logger.info("  ✓ All preset checks passed")
            
            return all_ok
            
        except Exception as e:
            logger.error(f"  ✗ Preset check failed: {e}")
            return False
    
    def generate_validation_report(self, results: dict) -> bool:
        """Generate validation report."""
        logger.info("\n" + "="*70)
        logger.info("📋 VALIDATION SUMMARY")
        logger.info("="*70)
        
        all_ok = True
        
        checks = [
            ("Database Integrity", results.get('database', False)),
            ("Excel Exports", results.get('excel', False)),
            ("Radar Charts", results.get('charts', False)),
            ("Composite Scores", results.get('scores', False)),
            ("Preset Results", results.get('presets', False))
        ]
        
        for check_name, passed in checks:
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"  {check_name:30} {status}")
            if not passed:
                all_ok = False
        
        logger.info("="*70)
        
        if all_ok:
            logger.info("\n✅ ALL VALIDATION CHECKS PASSED")
            logger.info("\nSprint 3 is ready for submission!")
        else:
            logger.warning("\n⚠ SOME CHECKS FAILED")
            logger.warning("Please address the issues above before submission")
        
        return all_ok
    
    def run(self):
        """Run full validation."""
        logger.info("\n" + "="*70)
        logger.info("🔍 SCREENER VALIDATION")
        logger.info("="*70)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        try:
            results = {
                'database': self.check_database(),
                'excel': self.check_excel_exports(),
                'charts': self.check_radar_charts(),
                'scores': self.check_composite_scores(),
                'presets': self.check_preset_results()
            }
            
            # Generate summary
            all_ok = self.generate_validation_report(results)
            
            logger.info(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*70 + "\n")
            
            return all_ok
            
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    validator = ScreenerValidator()
    success = validator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
