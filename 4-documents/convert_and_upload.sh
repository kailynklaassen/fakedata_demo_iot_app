#!/bin/bash
# Convert all .md in reports/docs/ -> .pdf in reports/pdfs/, then upload to UC volume
set -e

DOCS_DIR="/Users/kailyn.klaassen/synthetic_renewable_demo/reports/docs"
PDFS_DIR="/Users/kailyn.klaassen/synthetic_renewable_demo/reports/pdfs"
VOLUME_PATH="/Volumes/serverless_stable_cgxfyd_catalog/kailyn_klaassen/reports"
PROFILE="fe-vm-serverless-stable-cgxfyd"
MD2PDF="$HOME/.vibe/marketplace/plugins/fe-specialized-agents/skills/markdown-to-pdf/resources/markdown_to_pdf.py"

export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"

mkdir -p "$PDFS_DIR"

echo "=== Converting markdown to PDF ==="
n_md=$(ls "$DOCS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
echo "  found $n_md markdown files"

i=0
for md in "$DOCS_DIR"/*.md; do
  base=$(basename "$md" .md)
  pdf="$PDFS_DIR/$base.pdf"
  i=$((i+1))
  if [ -f "$pdf" ] && [ "$pdf" -nt "$md" ]; then
    echo "  [$i/$n_md] $base.pdf (cached)"
    continue
  fi
  uv run --python 3.12 --with weasyprint --with markdown --with pygments \
    python3 "$MD2PDF" --input "$md" --output "$pdf" > /dev/null 2>&1 && \
    echo "  [$i/$n_md] $base.pdf"
done

echo ""
echo "=== Uploading PDFs to UC Volume ==="
echo "  target: $VOLUME_PATH"
for pdf in "$PDFS_DIR"/*.pdf; do
  base=$(basename "$pdf")
  databricks fs cp --overwrite --profile="$PROFILE" "$pdf" "dbfs:$VOLUME_PATH/$base" > /dev/null 2>&1 && \
    echo "  uploaded $base"
done

echo ""
echo "=== Listing files in volume ==="
databricks fs ls "dbfs:$VOLUME_PATH" --profile="$PROFILE" | head -60
