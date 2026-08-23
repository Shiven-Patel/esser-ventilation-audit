#!/usr/bin/env bash
# Full pipeline. Every number and figure in docs/manuscript.md is regenerated here.
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/6] exposure";    python3 src/01_build_exposure.py
echo "[2/6] dataset";     python3 src/02_build_dataset.py
echo "[3/6] analysis";    python3 src/03_analysis.py
echo "[4/6] figures";     python3 src/04_figures.py
echo "[5/6] maps";        python3 src/07_maps.py
echo "[6/6] manuscript";  python3 src/05_math_doc.py && node src/06_manuscript_docx.js

echo
echo "Optional: interactive viewer   python3 src/08_build_viewer.py"
echo "Computed results:              output/analysis_log.md"
echo "Audit of the earlier pipeline: python3 src/00_audit_legacy.py --legacy-dataset <old csv>"
