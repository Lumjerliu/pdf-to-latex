#!/usr/bin/env python3
"""
Wrapper script to run Nougat on CPU (avoids MPS memory issues on Apple Silicon).
Outputs .tex files instead of .mmd
"""

import os
import sys
import shutil
from pathlib import Path

# Force CPU before importing torch
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"

# Disable MPS
import torch
torch.backends.mps.is_available = lambda: False
torch.backends.mps.is_built = lambda: False

# Now run nougat
from predict import main

if __name__ == "__main__":
    result = main()
    
    # After conversion, rename .mmd files to .tex
    output_dir = Path("output")
    for mmd_file in output_dir.glob("*.mmd"):
        tex_file = mmd_file.with_suffix(".tex")
        shutil.move(str(mmd_file), str(tex_file))
        print(f"Output: {tex_file}")
    
    sys.exit(result)
