from src.reports import portfolio_summary, sector_report, tearsheet
from src.analytics import capital_allocation
from src.nlp.pros_cons_generator import generate_pros_cons
from src.utils.pdf_utils import blank_pages, count_pages


def test_tearsheet_two_pages_no_blank_and_size(store, tmp_path):
    pc = generate_pros_cons(store)
    alloc = capital_allocation.latest_labels(store.table("capital_allocation"))
    results, skipped = tearsheet.batch_generate(store, pc, alloc, out_dir=tmp_path,
                                                tickers=["TCS", "M&M", "ZOMATO"], skipped_csv=tmp_path / "s.csv")
    assert {r["ticker"] for r in results} == {"TCS", "M&M"}            # ZOMATO has 2 years -> skipped
    assert list(skipped["ticker"]) == ["ZOMATO"]
    for r in results:
        assert count_pages(r["path"]) == 2
        assert blank_pages(r["path"]) == []
        assert r["path"].stat().st_size > 30 * 1024
        assert r["shrink"] >= tearsheet.SHRINK_WARN
    assert (tmp_path / "M_M_tearsheet.pdf").exists()


def test_sector_and_portfolio(store, tmp_path):
    paths = sector_report.batch_generate_sector_reports(store, out_dir=tmp_path)
    assert len(paths) == store.companies["sector"].nunique() == 11
    out = portfolio_summary.generate_portfolio_summary(store, tmp_path / "p.pdf")
    assert count_pages(out) == len(store.companies)
