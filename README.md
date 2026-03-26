# PDF to LaTeX Converter

Convert any PDF to LaTeX with one command.

## Installation

```bash
# 1. Clone and setup
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

### Option 1: One Command (Recommended)

```bash
# Put your PDF in the input folder, then:
./convert.sh input/your_file.pdf

# Or use any path:
./convert.sh ~/Desktop/paper.pdf
```

That's it! This creates:
- `output/your_file.tex` - LaTeX source
- `output/your_file.pdf` - Compiled PDF

### Option 2: Step by Step

```bash
# Step 1: OCR the PDF
CUDA_VISIBLE_DEVICES="" nougat your_file.pdf -o output/ --markdown

# Step 2: Convert to LaTeX
python3 md2tex.py output/your_file.mmd -o output/your_file.tex

# Step 3: Compile
cd output && tectonic your_file.tex
```

## Example

```bash
./convert.sh ~/Desktop/IMO2024SL.pdf
# Output: output/IMO2024SL.tex and output/IMO2024SL.pdf
```

## Tips

- **Apple Silicon (M1/M2/M3)**: The script automatically uses CPU to avoid memory issues
- **Edit the title**: Open `md2tex.py` and change the `\title{}` line
- **Large PDFs**: Processing takes ~1-2 minutes per page on CPU

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MPS out of memory | Script handles this automatically |
| albumentations error | `pip install albumentations==1.3.1` |
| transformers error | `pip install transformers==4.36.0` |

## Credits

- [Nougat](https://github.com/facebookresearch/nougat) by Meta AI
- [Tectonic](https://tectonic-typesetting.github.io/) LaTeX compiler
