#!/bin/bash
# CellSwarm v2 — Zenodo Package Script
# Creates archives for Zenodo upload:
#   1. Simulation output + analysis data
#   2. Figure source data + supplementary tables
#
# Usage: cd cellswarm-draft && bash scripts/package_zenodo.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_DIR="$HOME/Desktop"
TIMESTAMP=$(date +%Y%m%d)

echo "=== CellSwarm Zenodo Packaging ==="
echo "Project: $PROJECT_DIR"
echo ""

# --- Archive 1: Simulation output + analysis ---
echo "[1/2] Packaging simulation output + analysis data..."
ARCHIVE1="$OUTPUT_DIR/cellswarm-zenodo-simulation-${TIMESTAMP}.tar.gz"

tar -czf "$ARCHIVE1" \
  -C "$PROJECT_DIR" \
  03_simulation_output/ \
  04_analysis/deep_dive/

SIZE1=$(du -sh "$ARCHIVE1" | cut -f1)
COUNT1=$(tar -tzf "$ARCHIVE1" | grep -v '/$' | wc -l | tr -d ' ')
echo "  → $ARCHIVE1"
echo "  → $SIZE1, $COUNT1 files"
echo ""

# --- Archive 2: Figure source data + supplementary tables ---
echo "[2/2] Packaging figure source data + supplementary tables..."
ARCHIVE2="$OUTPUT_DIR/cellswarm-zenodo-figures-${TIMESTAMP}.tar.gz"

# Collect figure data CSVs and supplementary tables
cd "$PROJECT_DIR"
find 05_figures/fig*/data -name "*.csv" -o -name "*.json" 2>/dev/null | sort > /tmp/zenodo_fig_files.txt
find 05_figures/supplementary/tables -name "*.csv" 2>/dev/null | sort >> /tmp/zenodo_fig_files.txt

tar -czf "$ARCHIVE2" \
  -C "$PROJECT_DIR" \
  -T /tmp/zenodo_fig_files.txt

SIZE2=$(du -sh "$ARCHIVE2" | cut -f1)
COUNT2=$(tar -tzf "$ARCHIVE2" | grep -v '/$' | wc -l | tr -d ' ')
echo "  → $ARCHIVE2"
echo "  → $SIZE2, $COUNT2 files"
echo ""

rm -f /tmp/zenodo_fig_files.txt

# --- Summary ---
echo "=== Done ==="
echo "Archives created:"
echo "  $ARCHIVE1 ($SIZE1)"
echo "  $ARCHIVE2 ($SIZE2)"
echo ""
echo "Upload these to Zenodo along with metadata:"
echo "  Title: CellSwarm v2 — Simulation Data and Figure Source"
echo "  Keywords: agent-based modeling, tumor microenvironment, LLM, scRNA-seq"
