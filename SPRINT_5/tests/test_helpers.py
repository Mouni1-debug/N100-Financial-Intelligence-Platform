import math

from src.analytics.kpi_summary import trend_direction
from src.utils.helpers import cagr_pct, safe_filename, soft_break, strict_trend, trailing_streak


def test_cagr():
    assert round(cagr_pct(100, 200, 5), 2) == 14.87
    assert math.isnan(cagr_pct(-1, 200, 5))
    assert math.isnan(cagr_pct(100, 0, 5))


def test_streak_and_trend():
    assert trailing_streak([1, -1, 2, 3, 4], lambda v: v > 0) == 3
    assert strict_trend([1, 2, 3, 4], 3, "up")
    assert not strict_trend([1, 2, 2, 4], 3, "up")
    assert strict_trend([9, 7, 5, 3], 3, "down")


def test_filename_and_soft_break():
    assert safe_filename("M&M") == "M_M"
    assert safe_filename("Oil & Gas") == "Oil_Gas"
    assert " " in soft_break("A" * 50, 18)
    assert soft_break("short text") == "short text"


def test_trend_direction_polarity_and_flat_band():
    assert trend_direction(110, 100, True) == "up"
    assert trend_direction(90, 100, True) == "down"
    assert trend_direction(101.5, 100, True) == "flat"        # within 2 %
    assert trend_direction(0.8, 1.0, False) == "up"           # falling D/E = improvement
    assert trend_direction(1.2, 1.0, False) == "down"
    assert trend_direction(float("nan"), 1.0, True) is None
