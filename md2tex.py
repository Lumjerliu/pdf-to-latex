#!/usr/bin/env python3
"""
Convert Mathpix Markdown (Nougat output) to compilable LaTeX.
This converter is designed to handle common OCR artifacts and produce
clean, compilable LaTeX for any PDF.
"""

import re
import sys
import os

def convert_mmd_to_latex(input_file, output_file=None, title=None):
    """
    Convert Nougat's Mathpix Markdown output to compilable LaTeX.
    
    Args:
        input_file: Path to .mmd or .tex file from Nougat
        output_file: Output path (optional)
        title: Document title (optional, extracted from content if not provided)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ============================================
    # STEP 1: Remove OCR artifacts
    # ============================================
    
    # Remove MISSING_PAGE markers
    content = re.sub(r'\[MISSING_PAGE[^\]]*\]\n*', '', content)
    
    # Remove [0.5cm] markers
    content = content.replace('[0.5cm]', '\n\\vspace{0.5cm}\n')
    
    # Remove invalid \. commands (but keep valid ones like \vdots)
    content = re.sub(r'\\(?!vdots|dots|cdots|ldots|ddots)\.', '', content)
    
    # ============================================
    # STEP 2: Fix LaTeX command spacing
    # ============================================
    
    # Fix missing space after \angle: \angleD -> \angle D
    content = re.sub(r'\\angle([A-Z])', r'\\angle \1', content)
    
    # Fix missing space after other common commands
    for cmd in ['sin', 'cos', 'tan', 'log', 'ln', 'lim', 'max', 'min', 'sum', 'prod']:
        content = re.sub(rf'\\{cmd}([A-Za-z])', rf'\\{cmd} \1', content)
    
    # ============================================
    # STEP 3: Handle underscores (tricky!)
    # ============================================
    
    # Remove orphan underscores: number/letter followed by _ then letter
    # e.g., "2023_Sunday" -> "2023 Sunday"
    content = re.sub(r'([0-9.,;:!?\)\]])_([A-Za-z])', r'\1 \2', content)
    
    # Handle italic text _text_ (must have both underscores)
    def replace_italic(match):
        text = match.group(1)
        # Don't convert if it looks like a subscript
        if re.match(r'^[0-9]+$', text) or re.match(r'^[a-z]$', text):
            return match.group(0)  # Keep as is (likely subscript)
        return f'\\textit{{{text}}}'
    
    content = re.sub(r'_([A-Za-z][^_\n]+?)_(?![a-zA-Z0-9])', replace_italic, content)
    
    # Remove remaining orphan underscores at start of line
    content = re.sub(r'^_([A-Za-z])', r'\1', content, flags=re.MULTILINE)
    
    # Remove orphan underscores after space
    content = re.sub(r' _([A-Za-z])', r' \1', content)
    
    # ============================================
    # STEP 4: Fix broken math expressions
    # ============================================
    
    # Fix <*> pattern (OCR error in math)
    content = re.sub(r'<\*\s*\\?\(', r'\\) \\(', content)
    
    # Fix \)_ pattern (italic after math)
    content = re.sub(r'\\\)\s*_([^_]+?)_', r'\\) \\textit{\1}', content)
    
    # Remove truncated lines (ending with operator in math)
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that look truncated
        if re.search(r'\\\([^)]*[+\-*/<>=]$', stripped):
            continue
        if re.search(r'\$[^$]*[+\-*/<>=]$', stripped) and not re.search(r'\$[^$]*[+\-*/<>=]\$', stripped):
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # ============================================
    # STEP 5: Balance math delimiters
    # ============================================
    
    # Fix incomplete inline math \( \)
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        open_count = line.count('\\(')
        close_count = line.count('\\)')
        if open_count > close_count:
            line = line + '\\)' * (open_count - close_count)
        elif close_count > open_count:
            line = '\\(' * (close_count - open_count) + line
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # Remove incomplete display math \[ \]
    lines = content.split('\n')
    new_lines = []
    in_incomplete_math = False
    
    for line in lines:
        if '\\[' in line and '\\]' not in line:
            in_incomplete_math = True
            continue
        if in_incomplete_math:
            if '\\]' in line:
                in_incomplete_math = False
                continue
            elif line.startswith('##') or line.startswith('###'):
                in_incomplete_math = False
                new_lines.append(line)
            continue
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # ============================================
    # STEP 6: Convert Markdown to LaTeX
    # ============================================
    
    # Headers
    content = re.sub(r'^## (.+)$', r'\\section*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'\\subsection*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^# (.+)$', r'\\title{\1}', content, flags=re.MULTILINE)
    
    # Bold
    content = re.sub(r'\*\*([^*]+?)\*\*', r'\\textbf{\1}', content)
    
    # Bullet points
    content = re.sub(r'^<\*\s*', r'\\item ', content, flags=re.MULTILINE)
    content = re.sub(r'^\*\s+', r'\\item ', content, flags=re.MULTILINE)
    
    # Wrap \item in itemize
    lines = content.split('\n')
    new_lines = []
    in_itemize = False
    
    for line in lines:
        if line.strip().startswith('\\item'):
            if not in_itemize:
                new_lines.append('\\begin{itemize}')
                in_itemize = True
            new_lines.append(line)
        else:
            if in_itemize:
                new_lines.append('\\end{itemize}')
                in_itemize = False
            new_lines.append(line)
    
    if in_itemize:
        new_lines.append('\\end{itemize}')
    
    content = '\n'.join(new_lines)
    
    # ============================================
    # STEP 7: Convert math delimiters
    # ============================================
    
    # \( ... \) -> $ ... $
    content = content.replace('\\(', '$')
    content = content.replace('\\)', '$')
    
    # \[ ... \] -> equation* environment
    content = content.replace('\\[', '\n\\begin{equation*}')
    content = content.replace('\\]', '\\end{equation*}\n')
    
    # ============================================
    # STEP 8: Extract title if not provided
    # ============================================
    
    if not title:
        # Try to find a title in the first few lines
        first_lines = content[:500]
        title_match = re.search(r'\\title\{([^}]+)\}', first_lines)
        if title_match:
            title = title_match.group(1)
            content = re.sub(r'\\title\{[^}]+\}\n?', '', content, count=1)
        else:
            # Look for a date or problem set identifier
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December).*\d{4}', first_lines)
            if date_match:
                title = date_match.group(0).strip()
            else:
                title = "Converted Document"
    
    # ============================================
    # STEP 9: Create document
    # ============================================
    
    latex_doc = f'''% !TEX program = xelatex
\\documentclass[11pt,a4paper]{{article}}

\\usepackage{{fontspec}}
\\usepackage{{amsmath,amssymb,amsthm}}
\\usepackage{{mathtools}}
\\usepackage{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{enumitem}}
\\usepackage{{tikz}}
\\usetikzlibrary{{calc,arrows.meta}}

\\geometry{{margin=1in}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{0.5em}}
\\setcounter{{secnumdepth}}{{0}}

\\title{{{title}}}
\\author{{}}
\\date{{}}

\\begin{{document}}

\\maketitle

{content}

\\end{{document}}
'''
    
    if output_file is None:
        output_file = input_file.rsplit('.', 1)[0] + '_full.tex'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_doc)
    
    print(f"Converted: {input_file}")
    print(f"Output:    {output_file}")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 md2tex.py <input.mmd> [-o output.tex] [-t title]")
        print("\nConverts Nougat's Mathpix Markdown to compilable LaTeX.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    title = None
    
    # Parse arguments
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif args[i] == '-t' and i + 1 < len(args):
            title = args[i + 1]
            i += 2
        else:
            i += 1
    
    convert_mmd_to_latex(input_file, output_file, title)
