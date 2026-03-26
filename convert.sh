#!/bin/bash
# PDF to LaTeX Converter - One command to convert any PDF

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if PDF is provided
if [ -z "$1" ]; then
    echo "Usage: ./convert.sh <pdf_file>"
    echo ""
    echo "Examples:"
    echo "  ./convert.sh input/paper.pdf"
    echo "  ./convert.sh ~/Desktop/my_document.pdf"
    exit 1
fi

PDF_PATH="$1"
PDF_NAME=$(basename "$PDF_PATH" .pdf)

echo -e "${BLUE}Converting $PDF_NAME.pdf to LaTeX...${NC}"
echo ""

# Step 1: Convert PDF to Markdown+LaTeX using Nougat
echo -e "${BLUE}[1/3] Running Nougat OCR...${NC}"
CUDA_VISIBLE_DEVICES="" nougat "$PDF_PATH" -o output/ --markdown -m 0.1.0-small 2>/dev/null

# Find the output file (could be .mmd or .tex)
if [ -f "output/${PDF_NAME}.mmd" ]; then
    INPUT_FILE="output/${PDF_NAME}.mmd"
elif [ -f "output/${PDF_NAME}.tex" ]; then
    INPUT_FILE="output/${PDF_NAME}.tex"
else
    echo "Error: Could not find Nougat output"
    exit 1
fi

# Step 2: Convert to compilable LaTeX
echo -e "${BLUE}[2/3] Converting to LaTeX...${NC}"
python3 md2tex.py "$INPUT_FILE" -o "output/${PDF_NAME}.tex"

# Step 3: Compile to PDF
echo -e "${BLUE}[3/3] Compiling PDF...${NC}"
cd output
tectonic "${PDF_NAME}.tex" 2>/dev/null
cd ..

echo ""
echo -e "${GREEN}✓ Done!${NC}"
echo ""
echo "Output files:"
echo "  - output/${PDF_NAME}.tex  (LaTeX source)"
echo "  - output/${PDF_NAME}.pdf  (Compiled PDF)"
echo ""
echo "Open with: open output/${PDF_NAME}.pdf"
