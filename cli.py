#!/usr/bin/env python3
"""
Command-line interface for PDF to LaTeX converter.

Usage:
    python cli.py convert <pdf_path> [--output-dir DIR] [--format FORMAT] [--backend BACKEND]
    python cli.py batch <input_dir> [--output-dir DIR] [--format FORMAT]
    python cli.py info
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import json

from converter import PDFToLatexConverter, ConversionResult


def convert_command(args) -> int:
    """Handle the convert command."""
    pdf_path = Path(args.pdf_path)
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    output_dir = args.output_dir or str(pdf_path.parent / "output")
    
    print(f"Converting: {pdf_path}")
    print(f"Backend: {args.backend}")
    print(f"Output format: {args.format}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    converter = PDFToLatexConverter(backend=args.backend)
    result = converter.convert(
        str(pdf_path),
        output_dir=output_dir,
        output_format=args.format
    )
    
    if result.success:
        print(f"✓ Successfully converted {result.pages_processed} page(s)")
        
        output_file = Path(output_dir) / f"{pdf_path.stem}.tex"
        print(f"Output saved to: {output_file}")
        
        if args.preview:
            print("\n" + "=" * 50)
            print("PREVIEW:")
            print("=" * 50)
            preview_length = min(len(result.content), args.preview_length)
            print(result.content[:preview_length])
            if len(result.content) > preview_length:
                print(f"\n... ({len(result.content) - preview_length} more characters)")
        
        return 0
    else:
        print(f"✗ Conversion failed: {result.error_message}")
        return 1


def batch_command(args) -> int:
    """Handle the batch command for processing multiple PDFs."""
    input_dir = Path(args.input_dir)
    
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return 1
    
    output_dir = Path(args.output_dir or input_dir / "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in: {input_dir}")
        return 1
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    converter = PDFToLatexConverter(backend=args.backend)
    
    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}...", end=" ")
        
        result = converter.convert(
            str(pdf_path),
            output_dir=str(output_dir),
            output_format=args.format
        )
        
        if result.success:
            print(f"✓ ({result.pages_processed} pages)")
            results.append({
                "file": str(pdf_path),
                "success": True,
                "pages": result.pages_processed
            })
        else:
            print(f"✗ {result.error_message}")
            results.append({
                "file": str(pdf_path),
                "success": False,
                "error": result.error_message
            })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print("-" * 50)
    print(f"Completed: {successful}/{len(pdf_files)} files converted successfully")
    
    # Save results log
    log_file = output_dir / "conversion_log.json"
    with open(log_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Log saved to: {log_file}")
    
    return 0 if successful == len(pdf_files) else 1


def info_command(args) -> int:
    """Display information about available backends and system."""
    print("PDF to LaTeX Converter - Information")
    print("=" * 50)
    
    # Check backends
    backends = {
        "nougat": {
            "package": "nougat-ocr",
            "description": "Meta's model for scientific papers (recommended)",
            "best_for": "Academic papers, math, tables, multi-column layouts"
        },
        "texify": {
            "package": "texify",
            "description": "Excellent for math-heavy documents",
            "best_for": "Math equations, mixed text/equation documents"
        },
        "pix2tex": {
            "package": "pix2tex",
            "description": "Specialized for math equations",
            "best_for": "Single equations, math images"
        }
    }
    
    print("\nAvailable Backends:")
    print("-" * 50)
    
    for name, info in backends.items():
        try:
            __import__(name)
            status = "✓ installed"
        except ImportError:
            status = "✗ not installed"
        
        print(f"\n{name.upper()}:")
        print(f"  Package: {info['package']}")
        print(f"  Status: {status}")
        print(f"  Description: {info['description']}")
        print(f"  Best for: {info['best_for']}")
    
    # Check device
    print("\n" + "=" * 50)
    print("Device Information:")
    print("-" * 50)
    
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"CUDA: Available (GPU: {torch.cuda.get_device_name(0)})")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("MPS: Available (Apple Silicon)")
        else:
            print("GPU: Not available (using CPU)")
    except ImportError:
        print("PyTorch: Not installed")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF documents to LaTeX using open source OCR models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s convert paper.pdf
  %(prog)s convert paper.pdf --format latex --backend nougat
  %(prog)s batch ./papers --output-dir ./output
  %(prog)s info
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert a single PDF file")
    convert_parser.add_argument("pdf_path", help="Path to the PDF file")
    convert_parser.add_argument("--output-dir", "-o", help="Output directory")
    convert_parser.add_argument(
        "--format", "-f",
        choices=["markdown", "latex"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    convert_parser.add_argument(
        "--backend", "-b",
        choices=["nougat", "texify", "pix2tex"],
        default="nougat",
        help="OCR backend to use (default: nougat)"
    )
    convert_parser.add_argument(
        "--preview", "-p",
        action="store_true",
        help="Show preview of output"
    )
    convert_parser.add_argument(
        "--preview-length",
        type=int,
        default=1000,
        help="Preview length in characters (default: 1000)"
    )
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Convert multiple PDF files")
    batch_parser.add_argument("input_dir", help="Directory containing PDF files")
    batch_parser.add_argument("--output-dir", "-o", help="Output directory")
    batch_parser.add_argument(
        "--format", "-f",
        choices=["markdown", "latex"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    batch_parser.add_argument(
        "--backend", "-b",
        choices=["nougat", "texify", "pix2tex"],
        default="nougat",
        help="OCR backend to use (default: nougat)"
    )
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show system and backend information")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    if args.command == "convert":
        return convert_command(args)
    elif args.command == "batch":
        return batch_command(args)
    elif args.command == "info":
        return info_command(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
