# PDF to LaTeX Converter

Convert any PDF to LaTeX with one command. Uses Meta's Nougat OCR model.

## Installation

```bash
# Clone the repo
git clone https://github.com/Lumjerliu/pdf-to-latex.git
cd pdf-to-latex

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install albumentations==1.3.1 transformers==4.36.0

# Install LaTeX compiler (macOS)
brew install tectonic poppler
```

## Usage

### One Command

```bash
./convert.sh your_file.pdf
```

That's it! This creates:
- `output/your_file.tex` - LaTeX source
- `output/your_file.pdf` - Compiled PDF

### With Options

```bash
# Set a custom title
./convert.sh paper.pdf -t "My Research Paper"

# Use a different output directory
./convert.sh document.pdf -o results
```

### Step by Step (Manual)

```bash
# Step 1: OCR the PDF
CUDA_VISIBLE_DEVICES="" nougat your_file.pdf -o output/ -m 0.1.0-base

# Step 2: Convert to LaTeX
python3 md2tex.py output/your_file.mmd

# Step 3: Compile
cd output && tectonic your_file_full.tex
```

## What the Converter Handles

The `md2tex.py` converter automatically fixes:
- **OCR artifacts** - Missing pages, invalid commands
- **Math delimiters** - Converts `\( \)` to `$ $` and `\[ \]` to `equation*`
- **Markdown** - Headers, bold, italic, bullet points
- **Underscores** - Fixes orphan underscores that break LaTeX
- **Broken math** - Balances delimiters, removes truncated expressions
- **Command spacing** - Fixes `\angleD` → `\angle D`

## Tips

- **Apple Silicon (M1/M2/M3)**: The script automatically uses CPU to avoid memory issues
- **Large PDFs**: Processing takes ~1-2 minutes per page on CPU
- **Complex layouts**: The base model (`0.1.0-base`) is used for better accuracy
- **Diagrams**: Add TikZ code to the `.tex` file for geometry diagrams

## Files

| File | Purpose |
|------|---------|
| `convert.sh` | One-command converter script |
| `md2tex.py` | Markdown to LaTeX converter |
| `converter.py` | PDF conversion logic |
| `input/` | Put your PDFs here |
| `output/` | Generated files go here |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MPS out of memory | Script handles this automatically |
| albumentations error | `pip install albumentations==1.3.1` |
| transformers error | `pip install transformers==4.36.0` |
| Compilation errors | Check the `.tex` file for remaining issues |

## Credits

- [Nougat](https://github.com/facebookresearch/nougat) by Meta AI - OCR model
- [Tectonic](https://tectonic-typesetting.github.io/) - LaTeX compiler
