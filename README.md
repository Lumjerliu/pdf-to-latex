# PDF to LaTeX Converter

Convert PDF documents to compilable LaTeX using open source OCR models. This tool uses Meta's Nougat model to extract text, equations, and tables from PDFs and convert them to clean, compilable LaTeX.

## Features

- **Nougat OCR Model**: Meta's state-of-the-art model for scientific documents
- **Math Support**: Excellent handling of complex mathematical equations
- **Table Recognition**: Preserves table structures
- **Markdown to LaTeX Converter**: Converts Nougat's output to compilable LaTeX
- **CLI & Web Interface**: Multiple ways to use the tool
- **PDF Compilation**: Generates ready-to-compile LaTeX documents

## Complete Step-by-Step Guide

### Step 1: Prerequisites

Make sure you have the following installed:
- Python 3.9+ (check with `python3 --version`)
- Homebrew (for installing Tectonic LaTeX compiler)
- Git (for cloning/pushing to GitHub)

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/pdf-to-latex.git
cd pdf-to-latex

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows
```

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Fix compatibility issues (IMPORTANT!)
pip install albumentations==1.3.1
pip install transformers==4.36.0

# Install LaTeX compiler (Tectonic) - macOS only
brew install tectonic

# On Linux, use:
# curl -fsSL https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz | tar xz
# sudo mv tectonic /usr/local/bin/
```

### Step 4: Convert a PDF to LaTeX

#### Method A: Using Nougat Directly (Recommended)

```bash
# Force CPU usage (avoids memory issues on Apple Silicon)
CUDA_VISIBLE_DEVICES="" nougat your_document.pdf -o output/ --markdown -m 0.1.0-small
```

This creates `output/your_document.mmd` (Mathpix Markdown format).

#### Method B: Using the Python Script

```bash
# Convert PDF using the converter module
CUDA_VISIBLE_DEVICES="" python3 converter.py your_document.pdf output/
```

### Step 5: Convert Markdown to Compilable LaTeX

The Nougat output is in Mathpix Markdown format. Convert it to pure LaTeX:

```bash
python3 md2tex.py output/your_document.mmd -o output/your_document_full.tex
```

**Note**: If your file has a `.tex` extension already, use:
```bash
python3 md2tex.py output/your_document.tex -o output/your_document_full.tex
```

### Step 6: Compile LaTeX to PDF

```bash
cd output
tectonic your_document_full.tex
```

This generates `your_document_full.pdf`.

### Step 7: View the Result

```bash
# macOS
open your_document_full.pdf

# Linux
xdg-open your_document_full.pdf

# Windows
start your_document_full.pdf
```

## Quick Start Example

Here's a complete example converting a PDF to LaTeX:

```bash
# 1. Activate the virtual environment
cd pdf-to-latex
source venv/bin/activate

# 2. Convert PDF to Markdown+LaTeX (Nougat output)
CUDA_VISIBLE_DEVICES="" nougat ~/Desktop/my_paper.pdf -o output/ --markdown -m 0.1.0-small

# 3. Convert to pure LaTeX
python3 md2tex.py output/my_paper.mmd -o output/my_paper.tex

# 4. Compile to PDF
cd output && tectonic my_paper.tex

# 5. View the result
open my_paper.pdf
```

## The md2tex.py Converter

The `md2tex.py` script converts Nougat's Mathpix Markdown output to compilable LaTeX. It handles:

- **Math delimiters**: Converts `\( \)` to `$ $` and `\[ \]` to `equation*` environment
- **Headers**: Converts `## Header` to `\section*{Header}`
- **Bold/Italic**: Converts `**text**` to `\textbf{text}` and `_text_` to `\textit{text}`
- **Bullet points**: Wraps `* item` in `itemize` environment
- **OCR errors**: Fixes common OCR mistakes like missing spaces, broken math, etc.

### Usage

```bash
python3 md2tex.py input.mmd -o output.tex
```

### Customizing the Output

Edit the `md2tex.py` file to customize the document header:

```python
# Change the title, author, and date in the latex_doc template
\title{Your Document Title}
\author{Author Name}
\date{\today}
```

## Important Notes for Apple Silicon (M1/M2/M3) Users

The Nougat model can run out of memory on Apple Silicon GPUs (MPS). To avoid this:

```bash
# Force CPU usage (slower but stable)
CUDA_VISIBLE_DEVICES="" nougat your_file.pdf -o output/ --markdown
```

## OCR Backends

### Nougat (Recommended)
- **Best for**: Academic papers, scientific documents, math-heavy content
- **Strengths**: Tables, equations, multi-column layouts
- **Install**: `pip install nougat-ocr`
- **License**: MIT (code), CC-BY-NC (models)
- **Model sizes**: `0.1.0-small` (faster, less memory) or `0.1.0-base` (more accurate)

### Texify
- **Best for**: Math-heavy documents, mixed text/equation content
- **Strengths**: Outperforms Nougat on math benchmarks
- **Install**: `pip install texify`
- **License**: GPL-3.0

### pix2tex (LaTeX-OCR)
- **Best for**: Single equations, math images
- **Strengths**: Specialized equation recognition
- **Install**: `pip install pix2tex pdf2image`
- **License**: MIT

## Output Formats

### Markdown (Default)
Outputs Mathpix-compatible Markdown with embedded LaTeX:
```markdown
# Introduction

The equation $E = mc^2$ shows that...

$$\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}$$
```

### Pure LaTeX
Full LaTeX document ready for compilation:
```latex
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\section{Introduction}

The equation $E = mc^2$ shows that...

\begin{equation}
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
\end{equation}

\end{document}
```

## API Reference

### Python API

```python
from converter import PDFToLatexConverter, convert_pdf

# Simple conversion
result = convert_pdf("document.pdf", output_dir="./output")

# With options
converter = PDFToLatexConverter(backend="nougat", model_tag="0.1.0-small")
result = converter.convert(
    "document.pdf",
    output_dir="./output",
    output_format="latex"
)

if result.success:
    print(f"Converted {result.pages_processed} pages")
    print(result.content)
else:
    print(f"Error: {result.error_message}")
```

### REST API

```bash
# Upload and convert
curl -X POST -F "file=@document.pdf" http://localhost:5000/api/convert

# Check status
curl http://localhost:5000/api/status/<job_id>

# Download result
curl -O http://localhost:5000/api/download/<job_id>
```

## Hardware Requirements

- **CPU**: Works but slow (~2 min per page)
- **CUDA GPU**: Recommended for best performance
- **Apple Silicon (MPS)**: Supported but may run out of memory for complex documents

## Tips for Best Results

1. **Use Nougat for academic papers** - It's specifically trained on scientific documents
2. **Choose markdown format** - Easier to edit and review before final LaTeX
3. **Check equations manually** - OCR may make mistakes with complex notation
4. **Use `0.1.0-small` model** - Faster and uses less memory
5. **Force CPU on Apple Silicon** - Use `CUDA_VISIBLE_DEVICES=""` to avoid memory issues

## Troubleshooting

### "Backend not installed"
Install the required backend:
```bash
pip install nougat-ocr  # or texify, pix2tex
```

### "MPS backend out of memory"
Force CPU usage:
```bash
CUDA_VISIBLE_DEVICES="" nougat document.pdf -o output/
```

### "albumentations error"
Install compatible version:
```bash
pip install albumentations==1.3.1
```

### "transformers error"
Install compatible version:
```bash
pip install transformers==4.36.0
```

### Slow processing on CPU
Processing on CPU is slower but stable. For faster processing, consider using a machine with a CUDA GPU.

## Project Structure

```
pdf-to-latex/
├── app.py              # Flask web application
├── cli.py              # Command-line interface
├── converter.py        # Core conversion logic
├── md2tex.py           # Markdown to LaTeX converter
├── run_nougat.py       # CPU wrapper for Apple Silicon
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── static/
│   ├── css/
│   │   └── style.css   # Web UI styles
│   └── js/
│       └── app.js      # Frontend JavaScript
├── templates/
│   └── index.html      # Web UI template
├── uploads/            # Temporary upload storage
└── output/             # Conversion outputs
```

## Workflow Diagram

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PDF File  │────▶│  Nougat OCR      │────▶│  .mmd/.tex file │
│  (input)    │     │  (processing)    │     │  (Markdown+LaTeX)│
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PDF File  │◀────│  Tectonic        │◀────│  md2tex.py      │
│  (output)   │     │  (compilation)   │     │  (conversion)   │
└─────────────┘     └──────────────────┘     └─────────────────┘
```

## License

This project is open source. Individual OCR backends have their own licenses:
- Nougat: MIT (code), CC-BY-NC (models)
- Texify: GPL-3.0
- pix2tex: MIT

## Acknowledgments

- [Nougat](https://github.com/facebookresearch/nougat) by Meta AI
- [Texify](https://github.com/VikParuchuri/texify) by VikParuchuri
- [LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR) by lukas-blecher
