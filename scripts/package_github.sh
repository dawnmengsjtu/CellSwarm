#!/bin/bash
# CellSwarm v2 — GitHub Package Verification Script
# Verifies the repo is clean for GitHub push (code + small data only).
# Optionally creates a test archive to check size.
#
# Usage: cd cellswarm-draft && bash scripts/package_github.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=== CellSwarm GitHub Package Verification ==="
echo ""

# --- Check .gitignore exclusions ---
echo "[1/4] Checking .gitignore exclusions..."
ISSUES=0

if [ -d "06_paper/_archive" ]; then
  echo "  ⚠ 06_paper/_archive/ exists (excluded by .gitignore)"
fi
if [ -d "01_raw_data/external" ]; then
  SIZE=$(du -sh 01_raw_data/external/ | cut -f1)
  echo "  ⚠ 01_raw_data/external/ exists ($SIZE, excluded by .gitignore)"
fi
if find . -name ".DS_Store" 2>/dev/null | head -1 | grep -q .; then
  echo "  ⚠ .DS_Store files found — will be excluded by .gitignore"
  find . -name ".DS_Store" -delete 2>/dev/null && echo "    → Cleaned"
fi
if find . -name "__pycache__" -type d 2>/dev/null | head -1 | grep -q .; then
  echo "  ⚠ __pycache__/ directories found — will be excluded by .gitignore"
fi
echo ""

# --- Estimate GitHub repo size ---
echo "[2/4] Estimating GitHub repo size (excluding .gitignore patterns)..."

# Files that WILL be in GitHub
GITHUB_SIZE=$(du -sh \
  01_raw_data/knowledge_bases/ \
  01_raw_data/scRNAseq/ \
  02_code/ \
  03_simulation_output/ \
  04_analysis/ \
  05_figures/ \
  06_paper/main.tex \
  06_paper/main.pdf \
  06_paper/references.bib \
  06_paper/PAPER_DESIGN_v4.md \
  06_paper/sections/ \
  06_paper/tables/ \
  06_paper/figures/ \
  2>/dev/null | tail -1 | cut -f1)

echo "  Included content:"
echo "    01_raw_data/knowledge_bases/  $(du -sh 01_raw_data/knowledge_bases/ | cut -f1)"
echo "    01_raw_data/scRNAseq/         $(du -sh 01_raw_data/scRNAseq/ | cut -f1)"
echo "    02_code/                       $(du -sh 02_code/ | cut -f1)"
echo "    03_simulation_output/          $(du -sh 03_simulation_output/ | cut -f1)"
echo "    04_analysis/                   $(du -sh 04_analysis/ | cut -f1)"
echo "    05_figures/                    $(du -sh 05_figures/ | cut -f1)"
echo "    06_paper/ (excl _archive)      $(du -sh 06_paper/sections/ 06_paper/tables/ 06_paper/figures/ 06_paper/main.tex 06_paper/references.bib 2>/dev/null | tail -1 | cut -f1)"
echo ""

# --- Check for large files ---
echo "[3/4] Checking for files > 50 MB (GitHub limit: 100 MB per file)..."
LARGE=$(find . -not -path './01_raw_data/external/*' -not -path './.git/*' -not -path './06_paper/_archive/*' -type f -size +50M 2>/dev/null)
if [ -z "$LARGE" ]; then
  echo "  ✓ No files > 50 MB"
else
  echo "  ⚠ Large files found:"
  echo "$LARGE" | while read f; do
    echo "    $(du -sh "$f" | cut -f1)  $f"
  done
fi
echo ""

# --- List what goes to GitHub ---
echo "[4/4] GitHub content summary:"
echo "  Knowledge bases:     $(find 01_raw_data/knowledge_bases -name '*.yaml' | wc -l | tr -d ' ') YAML files"
echo "  Calibration data:    $(find 01_raw_data/scRNAseq -type f | wc -l | tr -d ' ') files"
echo "  Code:                $(find 02_code -type f | wc -l | tr -d ' ') files"
echo "  Simulation output:   $(find 03_simulation_output -name '*.json' | wc -l | tr -d ' ') JSON files"
echo "  Analysis:            $(find 04_analysis -type f | wc -l | tr -d ' ') files"
echo "  Figures:             $(find 05_figures -type f | wc -l | tr -d ' ') files"
echo "  Paper:               $(find 06_paper -not -path '*/\_archive/*' -type f | wc -l | tr -d ' ') files"
echo ""
echo "=== Ready for: git init && git add . && git commit && git push ==="
