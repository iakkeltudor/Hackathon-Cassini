"""
run_real_ingestion.py — full pipeline for real data.

Steps:
  1. (optional) ingest_study   — parse study CSV / PDF → study_clean.csv
  2.             ingest_sentinel — fetch Sentinel-2 via CDSE  → eo_clean.csv
  3.             merge_sources   — merge, feature-engineer, score
                                 → tarnita_predictions_scores.csv
                                 → storage/Excel.csv  (backend reads this)

Usage:
  python jobs/run_real_ingestion.py [--study PATH_TO_CSV_OR_PDF]
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion import ingest_study, ingest_sentinel
from processing import merge_sources
import config


def run(study_path: str | None = None) -> None:
    print("=" * 55)
    print("  RIPTIDE — REAL DATA INGESTION PIPELINE")
    print("=" * 55)

    # ── 1. Study data (optional) ───────────────────────────────────────────
    if study_path:
        if os.path.exists(study_path):
            print(f"\n[1/3] Processing study file: {study_path}")
            ingest_study.process_study_file(study_path)
        else:
            print(f"\n[1/3] Study file not found ({study_path}) — skipped.")
    else:
        study_clean = os.path.join(config.PROCESSED_DIR, "study_clean.csv")
        if os.path.exists(study_clean):
            print(f"\n[1/3] Using existing study_clean.csv")
        else:
            print("\n[1/3] No study data provided — in-situ columns will be empty.")

    # ── 2. Sentinel-2 ingestion ───────────────────────────────────────────
    print("\n[2/3] Sentinel-2 ingestion")
    eo_ok = ingest_sentinel.ingest_sentinel_data()

    eo_clean = os.path.join(config.PROCESSED_DIR, "eo_clean.csv")
    if not eo_ok and not os.path.exists(eo_clean):
        print("\n  ERROR: No EO data available and ingestion failed.")
        print("  Set CDSE_CLIENT_ID + CDSE_CLIENT_SECRET (or CDSE_USER + CDSE_PASSWORD)")
        print("  in pipelines/.env and re-run.")
        sys.exit(1)

    # ── 3. Merge, feature-engineer, score, export ─────────────────────────
    print("\n[3/3] Merge, feature engineering, scoring")
    df = merge_sources.run_full_merge_and_score()

    if df is None or df.empty:
        print("\n  ERROR: Pipeline produced no output.")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  PIPELINE COMPLETED")
    print(f"  Rows processed : {len(df)}")
    print(f"  Date range     : {df['Date'].min()} → {df['Date'].max()}")
    print(f"  Backend CSV    : {config.EXCEL_CSV_FILE}")
    print(f"  Visuals        : {config.VISUALS_DIR}/")
    print("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Riptide real data pipeline")
    parser.add_argument(
        "--study", type=str, default=None,
        help="Path to in-situ study file (CSV or PDF). Optional.",
    )
    args = parser.parse_args()
    run(args.study)
