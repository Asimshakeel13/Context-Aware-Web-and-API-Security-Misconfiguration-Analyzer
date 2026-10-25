#!/bin/bash
# Re-import the team planning PDFs (pdf/, git-ignored) into docs/project/.
# Run from the repo root:  bash docs/project/tools/import.sh
# Needs PyMuPDF (pip install pymupdf==1.25.1) and, for verify.py, pdftotext.
set -euo pipefail
PY="${PYTHON:-python3}"
TOOL="docs/project/tools/pdf2md.py"
STAMP="$(date +%F)"
while IFS='|' read -r src dst; do
  "$PY" "$TOOL" "pdf/$src" "docs/project/$dst" "Imported from the team PDF \`$src\` (local copy in \`pdf/\`, not committed). Converted to Markdown on $STAMP; tables and lists are kept, page headers dropped."
  echo "wrote docs/project/$dst"
done <<'LIST'
CAWASMA — Complete Project Summary (current).pdf|project-summary.md
CAWASMA — Revised Project Summary (old vs new).pdf|revised-summary-old-vs-new.md
CAWASMA — Software Requirements Specification.pdf|srs.md
CAWASMA — Requirements Specification & Development Plan.pdf|requirements-and-development-plan.md
CAWASMA — Per-Person Development Plan (3 partners).pdf|per-person-development-plan.md
CAWASMA_plan_atta.pdf|plan-atta.md
CAWASMA_plan_asim.pdf|plan-asim.md
CAWASMA_plan_neelam.pdf|plan-neelam.md
CAWASMA — Asim's Claude Code Prompts.pdf|prompts-asim.md
CAWASMA — Neelam's Claude Code Prompts.pdf|prompts-neelam.md
LIST
"$PY" docs/project/tools/verify.py
