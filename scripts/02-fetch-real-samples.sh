#!/usr/bin/env bash
# Download the two REAL public sample invoices used by the "harder documents" test.
# Source: https://huggingface.co/datasets/philschmid/pdf-samples (Apache 2.0). They contain generated/fake names.
# They are not stored in this repo; the expected values for them are in app/samples/real/ground-truth.json.
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/app/samples/real"
mkdir -p "$DEST"
for f in invoice.pdf invoice_with_scribbles.pdf; do
  curl -L -sS --fail -o "$DEST/hf-$f" "https://huggingface.co/datasets/philschmid/pdf-samples/resolve/main/$f"
  echo "downloaded $DEST/hf-$f ($(wc -c < "$DEST/hf-$f") bytes)"
done
echo "Expected sizes: hf-invoice.pdf about 560 KB, hf-invoice_with_scribbles.pdf about 106 KB."
