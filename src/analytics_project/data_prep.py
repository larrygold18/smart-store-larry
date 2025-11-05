"""
data_prep.py
------------
Reusable utilities for reading raw CSV files into pandas DataFrames.
First step of the BI/analytics pipeline.

Run from the project root:
    uv run python -m analytics_project.data_prep
    # or
    python -m analytics_project.data_prep
"""

from __future__ import annotations

from pathlib import Path
import logging
from typing import Dict
import pandas as pd

# Try a shared logger if you add one later; fall back to basic logging.
try:
    from .utils_logger import get_logger  # optional helper module

    logger = get_logger(__name__)
except Exception:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.warning("utils_logger not found; using basic logger.")

# --- Project paths ---
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_to_df(path: Path | str, **kwargs) -> pd.DataFrame:
    """Read a CSV into a DataFrame with sensible defaults and logging."""
    p = Path(path)
    if not p.exists():
        logger.error("File not found: %s", p)
        raise FileNotFoundError(p)

    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("low_memory", False)

    logger.info("Reading CSV: %s", p)
    df = pd.read_csv(p, **kwargs)
    logger.info("Loaded %s | rows=%s, cols=%s", p.name, df.shape[0], df.shape[1])
    return df


def read_all_csvs(
    directory: Path = RAW_DIR, pattern: str = "*.csv", **kwargs
) -> Dict[str, pd.DataFrame]:
    """Read all CSVs in a directory into a dict: filename -> DataFrame."""
    directory = Path(directory)
    if not directory.exists():
        logger.error("Directory does not exist: %s", directory)
        return {}

    csv_files = sorted(directory.glob(pattern))
    if not csv_files:
        logger.warning("No CSV files found in %s", directory)
        return {}

    frames: Dict[str, pd.DataFrame] = {}
    for csv_file in csv_files:
        try:
            frames[csv_file.name] = read_csv_to_df(csv_file, **kwargs)
        except Exception as e:
            logger.exception("Failed to load %s: %s", csv_file.name, e)
    return frames


def _save_shapes_summary(shapes: Dict[str, tuple[int, int]]) -> Path:
    """Write a small summary CSV (file, rows, cols) under data/processed."""
    out_path = PROCESSED_DIR / "_raw_file_shapes.csv"
    if shapes:
        pd.DataFrame(
            [(fname, r, c) for fname, (r, c) in shapes.items()],
            columns=["file", "rows", "cols"],
        ).to_csv(out_path, index=False)
        logger.info("Wrote shapes summary -> %s", out_path)
    else:
        logger.info("No shapes to summarize.")
    return out_path


def main() -> None:
    """Smoke test: read each CSV in data/raw, preview, and summarize shapes."""
    logger.info("Starting data prep smoke test…")

    frames = read_all_csvs(RAW_DIR)
    if not frames:
        logger.info("Nothing to process. Add CSVs to %s and re-run.", RAW_DIR)
        return

    shapes: Dict[str, tuple[int, int]] = {}
    for fname, df in frames.items():
        shapes[fname] = df.shape

        print(f"\n=== {fname} ===")
        print(f"Shape: {df.shape}")
        print(df.head(3))
        logger.info("✅ %s loaded: %s rows × %s cols", fname, *df.shape)

    summary_path = _save_shapes_summary(shapes)

    print("\n=== SUMMARY (file → (rows, cols)) ===")
    for fname, shp in shapes.items():
        print(f"{fname} → {shp}")
    print(f"\nSummary saved to: {summary_path}")

    logger.info("Smoke test complete for %s file(s).", len(shapes))


if __name__ == "__main__":
    main()
