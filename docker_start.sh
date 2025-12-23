#!/bin/sh
set -e

DATA_DIR="/app/data"

# Ensure data directory exists
if [ ! -d "$DATA_DIR" ]; then
  echo "ERROR: $DATA_DIR does not exist"
  echo "Run docker with -v <source_path>:/app/data"
  exit 1
fi


echo "Working directory {$(pwd)}"
# Run pdf generator only if MBOX_FILE is present
if [ -n "$MBOX_FILE" ]; then
  echo "MBOX_FILE detected: $MBOX_FILE"
  python extract_swiggy_pdfs.py "$MBOX_FILE"
  mv *.pdf ./data 2> /dev/null
else
  echo "MBOX_FILE not set, skipping extraction"
fi

VALIDATE_ONLY=${VALIDATE_ONLY:-$IGNORE}
# Run receipt_parser.py for each PDF file
found_pdf=false
for pdf in "$DATA_DIR"/*.pdf; do
  if [ -f "$pdf" ]; then
    found_pdf=true
    echo "Processing PDF: $pdf"
    python parse_receipts.py --schema instamart_schema.yaml "$pdf" $VALIDATE_ONLY > "$pdf.json"
  fi
done

if [ "$found_pdf" = false ]; then
  echo "No PDF files found in $DATA_DIR"
fi

echo "All processing complete."
