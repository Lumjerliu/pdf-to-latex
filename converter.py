"""
PDF to LaTeX Converter using Open Source OCR Models.

Supports multiple OCR backends:
- Nougat (Meta): Best for academic papers with math/tables
- Texify: Excellent for math-heavy documents
- pix2tex: Specialized for math equations
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a PDF to LaTeX conversion."""
    success: bool
    content: str
    output_format: str  # 'markdown' or 'latex'
    pages_processed: int
    error_message: Optional[str] = None


class PDFToLatexConverter:
    """
    Convert PDF documents to LaTeX using open source OCR models.
    
    Primary backend is Nougat (Meta's model) which excels at:
    - Scientific papers with complex math
    - Tables and figures
    - Multi-column layouts
    """
    
    def __init__(
        self,
        backend: Literal["nougat", "texify", "pix2tex"] = "nougat",
        model_tag: str = "0.1.0-small",
        device: Optional[str] = None
    ):
        """
        Initialize the converter.
        
        Args:
            backend: OCR backend to use ('nougat', 'texify', 'pix2tex')
            model_tag: Model tag for Nougat (e.g., '0.1.0-small', '0.1.0-base')
            device: Device to run on ('cuda', 'cpu', 'mps'). Auto-detected if None.
        """
        self.backend = backend
        self.model_tag = model_tag
        self.device = device or self._detect_device()
        self._check_dependencies()
    
    def _detect_device(self) -> str:
        """Detect the best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        dependencies = {
            "nougat": "nougat-ocr",
            "texify": "texify",
            "pix2tex": "pix2tex"
        }
        
        required = dependencies.get(self.backend)
        if required:
            try:
                __import__(self.backend)
                logger.info(f"Backend '{self.backend}' is available")
            except ImportError:
                logger.warning(
                    f"Backend '{self.backend}' not installed. "
                    f"Install with: pip install {required}"
                )
    
    def convert(
        self,
        pdf_path: str,
        output_dir: Optional[str] = None,
        output_format: Literal["markdown", "latex"] = "markdown",
        batch_size: int = 1,
        markdown: bool = True
    ) -> ConversionResult:
        """
        Convert a PDF file to LaTeX/Markdown.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save output (temp dir if None)
            output_format: Output format ('markdown' or 'latex')
            batch_size: Batch size for processing pages
            markdown: Output in markdown format (Nougat specific)
        
        Returns:
            ConversionResult with the converted content
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return ConversionResult(
                success=False,
                content="",
                output_format=output_format,
                pages_processed=0,
                error_message=f"PDF file not found: {pdf_path}"
            )
        
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if self.backend == "nougat":
                return self._convert_with_nougat(
                    pdf_path, output_dir, output_format, batch_size, markdown
                )
            elif self.backend == "texify":
                return self._convert_with_texify(pdf_path, output_dir)
            elif self.backend == "pix2tex":
                return self._convert_with_pix2tex(pdf_path, output_dir)
            else:
                return ConversionResult(
                    success=False,
                    content="",
                    output_format=output_format,
                    pages_processed=0,
                    error_message=f"Unknown backend: {self.backend}"
                )
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return ConversionResult(
                success=False,
                content="",
                output_format=output_format,
                pages_processed=0,
                error_message=str(e)
            )
    
    def _convert_with_nougat(
        self,
        pdf_path: Path,
        output_dir: Path,
        output_format: str,
        batch_size: int,
        markdown: bool
    ) -> ConversionResult:
        """Convert using Nougat CLI (most reliable method)."""
        # Use CLI as primary method - it's the most reliable
        return self._convert_with_nougat_cli(pdf_path, output_dir, output_format)
    
    def _convert_with_nougat_api(
        self,
        pdf_path: Path,
        output_dir: Path,
        output_format: str,
        batch_size: int,
        markdown: bool
    ) -> ConversionResult:
        """Convert using Nougat Python API (alternative method)."""
        try:
            from nougat.model import NougatModel
            from nougat.utils.checkpoint import get_checkpoint
            import torch
            
            # Load model
            checkpoint = get_checkpoint(model_tag=self.model_tag)
            model = NougatModel.from_pretrained(checkpoint)
            model.to(self.device)
            model.eval()
            
            # Process PDF pages
            from nougat.utils.dataset import NougatDataset
            from nougat.postprocessing import markdown_compatible
            
            dataset = NougatDataset(str(pdf_path))
            results = []
            
            with torch.no_grad():
                for sample in dataset:
                    output = model.inference(sample)
                    if markdown:
                        output = markdown_compatible(output)
                    results.append(output)
            
            content = "\n\n".join(results)
            
            # Save output as .tex
            output_file = output_dir / f"{pdf_path.stem}.tex"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            if output_format == "latex":
                content = self._markdown_to_latex(content)
            
            return ConversionResult(
                success=True,
                content=content,
                output_format=output_format,
                pages_processed=len(results)
            )
            
        except ImportError:
            # Fall back to CLI
            return self._convert_with_nougat_cli(pdf_path, output_dir, output_format)
    
    def _convert_with_nougat_cli(
        self,
        pdf_path: Path,
        output_dir: Path,
        output_format: str
    ) -> ConversionResult:
        """Convert using Nougat CLI (fallback)."""
        import os
        
        # Force CPU to avoid MPS memory issues on Apple Silicon
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = ""  # Force CPU
        
        cmd = [
            "nougat",
            str(pdf_path),
            "-o", str(output_dir),
            "--markdown",
            "-m", self.model_tag,
            "--recompute"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if result.returncode != 0:
            return ConversionResult(
                success=False,
                content="",
                output_format=output_format,
                pages_processed=0,
                error_message=f"Nougat CLI error: {result.stderr}"
            )
        
        # Read output (nougat outputs .mmd files)
        output_file = output_dir / f"{pdf_path.stem}.mmd"
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Rename to .tex
            tex_file = output_dir / f"{pdf_path.stem}.tex"
            import shutil
            shutil.move(str(output_file), str(tex_file))
            
            if output_format == "latex":
                content = self._markdown_to_latex(content)
            
            # Count pages (rough estimate)
            pages = content.count("[MISSING_PAGE") + content.count("\n\n") + 1
            
            return ConversionResult(
                success=True,
                content=content,
                output_format=output_format,
                pages_processed=pages
            )
        
        return ConversionResult(
            success=False,
            content="",
            output_format=output_format,
            pages_processed=0,
            error_message="Output file not created"
        )
    
    def _convert_with_texify(
        self,
        pdf_path: Path,
        output_dir: Path
    ) -> ConversionResult:
        """Convert using Texify model."""
        try:
            from texify.model import TexifyModel
            
            model = TexifyModel()
            content = model.predict(str(pdf_path))
            
            output_file = output_dir / f"{pdf_path.stem}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            return ConversionResult(
                success=True,
                content=content,
                output_format="markdown",
                pages_processed=1
            )
        except ImportError:
            return ConversionResult(
                success=False,
                content="",
                output_format="markdown",
                pages_processed=0,
                error_message="Texify not installed. Run: pip install texify"
            )
    
    def _convert_with_pix2tex(
        self,
        pdf_path: Path,
        output_dir: Path
    ) -> ConversionResult:
        """Convert using pix2tex (LaTeX-OCR) - best for single equations."""
        try:
            from pix2tex.cli import LatexOCR
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(str(pdf_path))
            
            model = LatexOCR()
            results = []
            
            for i, image in enumerate(images):
                latex = model(image)
                results.append(f"% Page {i+1}\n{latex}")
            
            content = "\n\n".join(results)
            
            output_file = output_dir / f"{pdf_path.stem}.tex"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            return ConversionResult(
                success=True,
                content=content,
                output_format="latex",
                pages_processed=len(images)
            )
        except ImportError as e:
            return ConversionResult(
                success=False,
                content="",
                output_format="latex",
                pages_processed=0,
                error_message=f"Missing dependency: {e}. Install with: pip install pix2tex pdf2image"
            )
    
    def _markdown_to_latex(self, markdown_content: str) -> str:
        """
        Convert Mathpix Markdown to pure LaTeX.
        
        Nougat outputs Mathpix Markdown which is Markdown with LaTeX math.
        This converts it to a LaTeX document.
        """
        lines = markdown_content.split("\n")
        latex_lines = []
        in_equation = False
        in_itemize = False
        
        for line in lines:
            # Handle display math
            if line.strip().startswith("$$"):
                if in_equation:
                    latex_lines.append("\\end{equation}")
                    in_equation = False
                else:
                    latex_lines.append("\\begin{equation}")
                    in_equation = True
                continue
            
            # Handle inline math (already LaTeX)
            # Handle headers
            if line.startswith("# "):
                latex_lines.append(f"\\section{{{line[2:]}}}")
            elif line.startswith("## "):
                latex_lines.append(f"\\subsection{{{line[3:]}}}")
            elif line.startswith("### "):
                latex_lines.append(f"\\subsubsection{{{line[4:]}}}")
            # Handle lists
            elif line.startswith("- ") or line.startswith("* "):
                if not in_itemize:
                    latex_lines.append("\\begin{itemize}")
                    in_itemize = True
                latex_lines.append(f"  \\item {line[2:]}")
            else:
                if in_itemize and not (line.startswith("- ") or line.startswith("* ")):
                    latex_lines.append("\\end{itemize}")
                    in_itemize = False
                latex_lines.append(line)
        
        if in_itemize:
            latex_lines.append("\\end{itemize}")
        
        # Wrap in document
        content = "\n".join(latex_lines)
        latex_document = f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{graphicx}}

\\begin{{document}}

{content}

\\end{{document}}
"""
        return latex_document


def convert_pdf(
    pdf_path: str,
    output_dir: Optional[str] = None,
    backend: str = "nougat",
    output_format: str = "markdown"
) -> ConversionResult:
    """
    Convenience function to convert a PDF.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory
        backend: OCR backend ('nougat', 'texify', 'pix2tex')
        output_format: 'markdown' or 'latex'
    
    Returns:
        ConversionResult with the converted content
    """
    converter = PDFToLatexConverter(backend=backend)
    return converter.convert(pdf_path, output_dir, output_format)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python converter.py <pdf_path> [output_dir]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = convert_pdf(pdf_path, output_dir)
    
    if result.success:
        print(f"Successfully converted {result.pages_processed} pages")
        print(f"Output format: {result.output_format}")
        print("\nContent preview:")
        print("-" * 40)
        print(result.content[:500] + "..." if len(result.content) > 500 else result.content)
    else:
        print(f"Conversion failed: {result.error_message}")
