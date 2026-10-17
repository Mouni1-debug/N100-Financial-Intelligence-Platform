"""Render page images of the 5 test tearsheets for the visual spot-check
(requires poppler's `pdftoppm`).   python scripts/render_previews.py"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings  # noqa: E402

if __name__ == "__main__":
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm not found - install poppler-utils to render previews.")
    out = settings.REPORTS_DIR / "previews"
    out.mkdir(exist_ok=True)
    for pdf in sorted(settings.TEARSHEET_TEST_DIR.glob("*_tearsheet.pdf")):
        subprocess.run(["pdftoppm", "-png", "-r", "70", str(pdf), str(out / pdf.stem)], check=True)
    print(f"Previews written to {out}")
