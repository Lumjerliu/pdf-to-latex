# PDF to LaTeX Converter

Convert any PDF to LaTeX using AI. Perfect for academic papers, math documents, and scientific articles.

## What This Does

```
PDF → Nougat OCR → Markdown+LaTeX → Pure LaTeX → PDF
```

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/Lumjerliu/pdf-to-latex.git
cd pdf-to-latex

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install albumentations==1.3.1 transformers==4.36.0

# 4. Install LaTeX compiler (macOS)
brew install tectonic
```

## Usage

### Step 1: Convert PDF to Markdown+LaTeX

```bash
CUDA_VISIBLE_DEVICES="" nougat your_file.pdf -o output/ --markdown -m 0.1.0-small
```

This creates `output/your_file.mmd` (or `.tex`).

### Step 2: Convert to Compilable LaTeX

```bash
python3 md2tex.py output/your_file.mmd -o output/your_file.tex
```

### Step 3: Compile to PDF

```bash
cd output
tectonic your_file.tex
```

Done! Open `your_file.pdf` to see the result.

## Example

```bash
# Convert a paper
CUDA_VISIBLE_DEVICES="" nougat paper.pdf -o output/ --markdown

# Make it compilable
python3 md2tex.py output/paper.mmd -o output/paper.tex

# Compile
cd output && tectonic paper.tex && open paper.pdf
```

## Tips

- **Apple Silicon (M1/M2/M3)**: Always use `CUDA_VISIBLE_DEVICES=""` to force CPU and avoid memory issues
- **Large PDFs**: Use `-m 0.1.0-small` for faster processing
- **Edit the title**: Open `md2tex.py` and change the `\title{}` line

## Project Files

| File | Purpose |
|------|---------|
| `converter.py` | PDF conversion logic |
| `md2tex.py` | Markdown to LaTeX converter |
| `app.py` | Web interface (optional) |
| `requirements.txt` | Python dependencies |

## Troubleshooting

**"MPS out of memory"** → Add `CUDA_VISIBLE_DEVICES=""` before the command

**"albumentations error"** → Run `pip install albumentations==1.3.1`

**"transformers error"** → Run `pip install transformers==4.36.0`

**Slow processing** → CPU is slower but stable. Use a CUDA GPU for speed.

## Credits

- [Nougat](https://github.com/facebookresearch/nougat) by Meta AI - The OCR model
- [Tectonic](https://tectonic-typesetting.github.io/) - LaTeX compiler
