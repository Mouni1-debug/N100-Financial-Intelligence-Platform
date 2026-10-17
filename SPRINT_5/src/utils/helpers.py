"""Small, dependency-light numeric and string helpers shared by all modules."""
from __future__ import annotations

import math
import re
from typing import Callable, Iterable

import pandas as pd

NAN = float("nan")


def is_nan(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or bool(pd.isna(value))


def clip01(value) -> float:
    """Clamp a number into [0, 1]; NaN becomes 0."""
    if is_nan(value):
        return 0.0
    return float(min(1.0, max(0.0, value)))


def safe_div(numerator, denominator) -> float:
    try:
        if is_nan(numerator) or is_nan(denominator) or denominator == 0:
            return NAN
        return float(numerator) / float(denominator)
    except (TypeError, ValueError):
        return NAN


def cagr_pct(start, end, years: int) -> float:
    """Compound annual growth rate in percent; NaN when undefined."""
    if is_nan(start) or is_nan(end) or years <= 0 or start <= 0 or end <= 0:
        return NAN
    return ((end / start) ** (1.0 / years) - 1.0) * 100.0


def trailing_streak(values: Iterable, predicate: Callable[[float], bool]) -> int:
    """Number of consecutive items (counted from the end) satisfying ``predicate``."""
    count = 0
    for v in reversed(list(values)):
        if not is_nan(v) and predicate(v):
            count += 1
        else:
            break
    return count


def strict_trend(values: Iterable, changes: int, direction: str) -> bool:
    """True if the last ``changes`` year-over-year moves are all strictly up/down."""
    vals = [v for v in list(values) if not is_nan(v)]
    if len(vals) < changes + 1:
        return False
    tail = vals[-(changes + 1):]
    diffs = [b - a for a, b in zip(tail, tail[1:])]
    return all(d > 0 for d in diffs) if direction == "up" else all(d < 0 for d in diffs)


def safe_filename(text: str) -> str:
    """Make a ticker / sector name safe to use inside a file name (e.g. M&M -> M_M)."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(text)).strip("_")


def soft_break(text: str, max_token: int = 18) -> str:
    """Insert spaces into unbroken tokens longer than ``max_token`` characters so that
    table cells can always wrap them (guards against overflow from very long strings)."""
    def _split(match):
        token = match.group(0)
        return " ".join(token[i:i + max_token] for i in range(0, len(token), max_token))
    return re.sub(r"\S{%d,}" % (max_token + 1), _split, str(text))
