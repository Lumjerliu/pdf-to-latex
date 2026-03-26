#!/bin/bash
# PDF to LaTeX Converter - Converts any PDF to LaTeX
# Usage: ./convert.sh <pdf_file> [-t "Title"]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
PDF_PATH=""
TITLE=""
OUTPUT_DIR="output"

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        *)
            PDF_PATH="$1"
            shift
            ;;
    esac
done

# Check if PDF is provided
if [ -z "$PDF_PATH" ]; then
    echo "Usage: ./convert.sh <pdf_file> [-t \"Title\"] [-o output_dir]"
    echo ""
    echo "Options:"
    echo "  -t, --title   Set document title"
    echo "  -o, --output  Output directory (default: output)"
    echo ""
    echo "Examples:"
    echo "  ./convert.sh document.pdf"
    echo "  ./convert.sh paper.pdf -t \"My Paper\""
    echo "  ./convert.sh ~/Desktop/IMO2023.pdf -o results"
    exit 1
fi

# Get PDF name without extension
PDF_NAME=$(basename "$PDF_PATH" .pdf)
PDF_DIR=$(dirname "$PDF_PATH")

echo -e "${BLUE}Converting $PDF_NAME.pdf to LaTeX...${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/pages"

# Step 1: Convert PDF to Markdown+LaTeX using Nougat
echo -e "${BLUE}[1/3] Running Nougat OCR (this may take a while)...${NC}"

# Use base model for better accuracy
CUDA_VISIBLE_DEVICES="" nougat "$PDF_PATH" -o "$OUTPUT_DIR/pages" -m 0.1.0-base --recompute 2>/dev/null

# Find and combine all .mmd files
COMBINED_MMD="$OUTPUT_DIR/${PDF_NAME}.mmd"
cat "$OUTPUT_DIR/pages"/*.mmd 2>/dev/null > "$COMBINED_MMD" || true

# Check if we got output
if [ ! -s "$COMBINED_MMD" ]; then
    # Try with the original output location
    if [ -f "$OUTPUT_DIR/${PDF_NAME}.mmd" ]; then
        COMBINED_MMD="$OUTPUT_DIR/${PDF_NAME}.mmd"
    else
        echo -e "${RED}Error: Nougat did not produce any output${NC}"
        exit 1
    fi
fi

# Step 2: Convert to compilable LaTeX
echo -e "${BLUE}[2/3] Converting to LaTeX...${NC}"

TEX_OUTPUT="$OUTPUT_DIR/${PDF_NAME}.tex"

if [ -n "$TITLE" ]; then
    python3 md2tex.py "$COMBINED_MMD" -o "$TEX_OUTPUT" -t "$TITLE"
else
    python3 md2tex.py "$COMBINED_MMD" -o "$TEX_OUTPUT"
fi

# Step 3: Compile to PDF
echo -e "${BLUE}[3/3] Compiling PDF...${NC}"

cd "$OUTPUT_DIR"
if tectonic "${PDF_NAME}.tex" 2>/dev/null; then
    cd - > /dev/null
    echo ""
    echo -e "${GREEN}✓ Done!${NC}"
    echo ""
    echo "Output files:"
    echo "  - $OUTPUT_DIR/${PDF_NAME}.tex  (LaTeX source)"
    echo "  - $OUTPUT_DIR/${PDF_NAME}.pdf  (Compiled PDF)"
    echo ""
    echo "Open with: open $OUTPUT_DIR/${PDF_NAME}.pdf"
else
    cd - > /dev/null
    echo -e "${RED}Compilation had errors. Check the .tex file manually.${NC}"
    echo "LaTeX source: $OUTPUT_DIR/${PDF_NAME}.tex"
fi
