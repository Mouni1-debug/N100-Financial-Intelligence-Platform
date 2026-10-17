"""Create a synthetic dataset in data/ so the pipeline can be demonstrated end-to-end.

    python scripts/generate_sample_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.sample_data import generate_dataset, write_dataset  # noqa: E402

if __name__ == "__main__":
    frames = generate_dataset()
    write_dataset(frames)
    print(f"Sample data written: {len(frames['companies'])} companies, "
          f"{len(frames['profit_loss'])} P&L rows.")
