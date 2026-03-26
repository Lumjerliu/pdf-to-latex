# PDF/Image to LaTeX Converter

Convert any PDF or image to LaTeX with one command. Uses Meta's Nougat OCR model.

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

# Install LaTeX compiler and tools (macOS)
brew install tectonic poppler imagemagick
```

## Usage

### One Command

```bash
# Convert a PDF
./convert.sh document.pdf

# Convert an image
./convert.sh equation.png

# Convert any image format
./convert.sh screenshot.jpg
./convert.sh scan.tiff
```

Output:
- `output/filename.tex` - LaTeX source
- `output/filename.pdf` - Compiled PDF

### With Options

```bash
# Set a custom title
./convert.sh paper.pdf -t "My Research Paper"

# Use a different output directory
./convert.sh image.png -o results
```

### Step by Step (Manual)

```bash
# Step 1: OCR the file
CUDA_VISIBLE_DEVICES="" nougat your_file.pdf -o output/ -m 0.1.0-base

# Step 2: Convert to LaTeX
python3 md2tex.py output/your_file.mmd

# Step 3: Compile
cd output && tectonic your_file_full.tex
```

## Supported Formats

| Type | Extensions |
|------|------------|
| PDF | `.pdf` |
| Images | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` |

## What the Converter Handles

The `md2tex.py` converter automatically fixes:
- **OCR artifacts** - Missing pages, invalid commands
- **Math delimiters** - Converts `\( \)` to `$ $` and `\[ \]` to `equation*`
- **Markdown** - Headers, bold, italic, bullet points
- **Underscores** - Fixes orphan underscores that break LaTeX
- **Broken math** - Balances delimiters, removes truncated expressions
- **Command spacing** - Fixes `\angleD` → `\angle D`

## Tips

- **Apple Silicon (M1/M2/M3)**: Script automatically uses CPU to avoid memory issues
- **Large PDFs**: Processing takes ~1-2 minutes per page on CPU
- **Complex layouts**: Base model (`0.1.0-base`) is used for better accuracy
- **Images with equations**: Works great for math screenshots
- **Diagrams**: Add TikZ code to the `.tex` file for geometry diagrams

## Files

| File | Purpose |
|------|---------|
| `convert.sh` | One-command converter (PDF + images) |
| `md2tex.py` | Markdown to LaTeX converter |
| `converter.py` | PDF conversion logic |
| `input/` | Put your files here |
| `output/` | Generated files go here |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MPS out of memory | Script handles this automatically |
| albumentations error | `pip install albumentations==1.3.1` |
| transformers error | `pip install transformers==4.36.0` |
| Image not recognized | Ensure imagemagick is installed |
| Compilation errors | Check the `.tex` file for remaining issues |

## Credits

- [Nougat](https://github.com/facebookresearch/nougat) by Meta AI - OCR model
- [Tectonic](https://tectonic-typesetting.github.io/) - LaTeX compiler
- [ImageMagick](https://imagemagick.org/) - Image processing
