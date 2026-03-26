#!/bin/bash
# PDF/Image to LaTeX Converter - Converts any PDF or image to LaTeX
# Usage: ./convert.sh <file> [-t "Title"]
# Supports: PDF, PNG, JPG, JPEG, TIFF, BMP

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
INPUT_PATH=""
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
            INPUT_PATH="$1"
            shift
            ;;
    esac
done

# Check if file is provided
if [ -z "$INPUT_PATH" ]; then
    echo "Usage: ./convert.sh <file> [-t \"Title\"] [-o output_dir]"
    echo ""
    echo "Supported formats: PDF, PNG, JPG, JPEG, TIFF, BMP"
    echo ""
    echo "Options:"
    echo "  -t, --title   Set document title"
    echo "  -o, --output  Output directory (default: output)"
    echo ""
    echo "Examples:"
    echo "  ./convert.sh document.pdf"
    echo "  ./convert.sh image.png -t \"Equation\""
    echo "  ./convert.sh ~/Desktop/screenshot.jpg"
    exit 1
fi

# Check if file exists
if [ ! -f "$INPUT_PATH" ]; then
    echo -e "${RED}Error: File not found: $INPUT_PATH${NC}"
    exit 1
fi

# Get file info
FILE_NAME=$(basename "$INPUT_PATH")
FILE_EXT="${FILE_NAME##*.}"
FILE_BASE="${FILE_NAME%.*}"
FILE_EXT_LOWER=$(echo "$FILE_EXT" | tr '[:upper:]' '[:lower:]')

# Create output directory
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/pages"

echo -e "${BLUE}Converting $FILE_NAME to LaTeX...${NC}"
echo ""

# Determine file type and process accordingly
if [[ "$FILE_EXT_LOWER" == "pdf" ]]; then
    # ===== PDF PROCESSING =====
    echo -e "${BLUE}[1/3] Running Nougat OCR on PDF...${NC}"
    
    CUDA_VISIBLE_DEVICES="" nougat "$INPUT_PATH" -o "$OUTPUT_DIR/pages" -m 0.1.0-base --recompute 2>/dev/null
    
    # Combine all .mmd files
    COMBINED_MMD="$OUTPUT_DIR/${FILE_BASE}.mmd"
    cat "$OUTPUT_DIR/pages"/*.mmd 2>/dev/null > "$COMBINED_MMD" || true
    
    if [ ! -s "$COMBINED_MMD" ]; then
        if [ -f "$OUTPUT_DIR/${FILE_BASE}.mmd" ]; then
            COMBINED_MMD="$OUTPUT_DIR/${FILE_BASE}.mmd"
        else
            echo -e "${RED}Error: Nougat did not produce any output${NC}"
            exit 1
        fi
    fi
    
else
    # ===== IMAGE PROCESSING =====
    echo -e "${BLUE}[1/3] Running Nougat OCR on image...${NC}"
    
    # Nougat can process images directly
    COMBINED_MMD="$OUTPUT_DIR/${FILE_BASE}.mmd"
    
    CUDA_VISIBLE_DEVICES="" nougat "$INPUT_PATH" -o "$OUTPUT_DIR" -m 0.1.0-base --recompute 2>/dev/null
    
    # Check for output
    if [ ! -f "$COMBINED_MMD" ]; then
        # Try with pages subdirectory
        if [ -f "$OUTPUT_DIR/pages/${FILE_BASE}.mmd" ]; then
            COMBINED_MMD="$OUTPUT_DIR/pages/${FILE_BASE}.mmd"
        else
            echo -e "${RED}Error: Nougat did not produce any output${NC}"
            echo "Trying alternative method..."
            
            # Alternative: Convert image to PDF first
            TEMP_PDF="$OUTPUT_DIR/temp.pdf"
            magick "$INPUT_PATH" "$TEMP_PDF" 2>/dev/null || convert "$INPUT_PATH" "$TEMP_PDF" 2>/dev/null || true
            
            if [ -f "$TEMP_PDF" ]; then
                echo -e "${BLUE}Converted image to PDF, running OCR...${NC}"
                CUDA_VISIBLE_DEVICES="" nougat "$TEMP_PDF" -o "$OUTPUT_DIR" -m 0.1.0-base --recompute 2>/dev/null
                rm -f "$TEMP_PDF"
                COMBINED_MMD="$OUTPUT_DIR/temp.mmd"
            fi
            
            if [ ! -f "$COMBINED_MMD" ]; then
                echo -e "${RED}Error: Could not process image${NC}"
                exit 1
            fi
        fi
    fi
fi

# Step 2: Convert to compilable LaTeX
echo -e "${BLUE}[2/3] Converting to LaTeX...${NC}"

TEX_OUTPUT="$OUTPUT_DIR/${FILE_BASE}.tex"

if [ -n "$TITLE" ]; then
    python3 md2tex.py "$COMBINED_MMD" -o "$TEX_OUTPUT" -t "$TITLE"
else
    python3 md2tex.py "$COMBINED_MMD" -o "$TEX_OUTPUT"
fi

# Step 3: Compile to PDF
echo -e "${BLUE}[3/3] Compiling PDF...${NC}"

cd "$OUTPUT_DIR"
if tectonic "${FILE_BASE}.tex" 2>/dev/null; then
    cd - > /dev/null
    echo ""
    echo -e "${GREEN}✓ Done!${NC}"
    echo ""
    echo "Output files:"
    echo "  - $OUTPUT_DIR/${FILE_BASE}.tex  (LaTeX source)"
    echo "  - $OUTPUT_DIR/${FILE_BASE}.pdf  (Compiled PDF)"
    echo ""
    echo "Open with: open $OUTPUT_DIR/${FILE_BASE}.pdf"
else
    cd - > /dev/null
    echo -e "${RED}Compilation had errors. Check the .tex file manually.${NC}"
    echo "LaTeX source: $OUTPUT_DIR/${FILE_BASE}.tex"
fi
