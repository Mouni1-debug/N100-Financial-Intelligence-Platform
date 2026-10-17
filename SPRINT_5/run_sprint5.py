#!/usr/bin/env python
"""Sprint 5 command-line entry point.

Examples
--------
    python run_sprint5.py --sample-data --day all     # demo with synthetic data
    python run_sprint5.py --day 30                    # only the pros/cons generator
    python run_sprint5.py --day 33 --tickers TCS INFY # tearsheet layout test
"""
from __future__ import annotations

import argparse
import sys

from config import settings
from src import pipeline
from src.utils.data_loader import DataStore, DataValidationError
from src.utils.logger import get_logger

log = get_logger("run_sprint5")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="N100 Financial Intelligence Platform - Sprint 5")
    ap.add_argument("--day", default="all", help="29..35 or 'all' (default: all)")
    ap.add_argument("--tickers", nargs="*", help="Day 33 only: tickers for the layout test")
    ap.add_argument("--sample-data", action="store_true", help="Generate synthetic input data first")
    args = ap.parse_args(argv)

    settings.ensure_directories()
    if args.sample_data:
        from src.utils.sample_data import generate_dataset, write_dataset
        write_dataset(generate_dataset())
        log.info("Synthetic sample data written to data/")

    store = DataStore()
    try:
        if args.day == "all":
            pipeline.run_all(store)
        else:
            day = int(args.day)
            if day not in pipeline.STEPS:
                ap.error("--day must be one of 29-35 or 'all'")
            if day == 33:
                pipeline.run_day33(store, args.tickers)
            else:
                pipeline.STEPS[day](store)
    except DataValidationError as exc:
        log.error("Input data problem: %s", exc)
        log.error("Tip: run with --sample-data to try the pipeline with synthetic data.")
        return 2
    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
