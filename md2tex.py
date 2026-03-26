#!/usr/bin/env python3
"""Convert Mathpix Markdown to proper LaTeX document."""

import re
import sys

def convert_mmd_to_latex(input_file, output_file=None):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove MISSING_PAGE markers
    content = re.sub(r'\[MISSING_PAGE[^\]]*\]\n*', '', content)
    
    # Remove [0.5cm] markers
    content = content.replace('[0.5cm]', '\n\\vspace{0.5cm}\n')
    
    # Fix invalid LaTeX patterns
    content = content.replace('\\vdots\\.\\]', '\\vdots\\]')  # Fix \vdots\.\] -> \vdots\]
    content = content.replace('\\.', '')  # Remove other invalid \. commands
    content = content.replace('\\)_._', '\\).')  # Fix \)_._ -> \).
    
    # Fix missing space after \angle: \angleD -> \angle D
    content = re.sub(r'\\angle([A-Z])', r'\\angle \1', content)
    
    # Handle italic text _text_ (full pattern with both underscores)
    # This handles patterns like _Saturday, 8. July 2023_
    content = re.sub(r'_([A-Za-z][^_]+?)_', r'\\textit{\1}', content)
    
    # Remove orphan underscores at start of line (not part of a pair)
    # Pattern: _Word at start of line without closing underscore
    content = re.sub(r'^_([A-Za-z])', r'\1', content, flags=re.MULTILINE)
    
    # Remove orphan underscores after space (not part of a pair)
    content = re.sub(r' _([A-Za-z])', r' \1', content)
    
    # Fix pattern: \) _ text _ -> \) \textit{text} (with space before _)
    while '\\) _' in content:
        start = content.find('\\) _')
        if start == -1:
            break
        end = content.find('_', start + 4)
        if end == -1:
            break
        text = content[start+4:end]
        content = content[:start] + '\\) \\textit{' + text + '}' + content[end+1:]
    
    # Fix pattern: \)_ text _ -> \) \textit{text} (without space)
    while '\\)_' in content:
        start = content.find('\\)_')
        if start == -1:
            break
        end = content.find('_', start + 3)
        if end == -1:
            break
        text = content[start+3:end]
        content = content[:start] + '\\) \\textit{' + text + '}' + content[end+1:]
    
    # Fix broken math expressions with <*> pattern FIRST
    content = re.sub(r'<\*\s+\\?\(', r'\\) \\(', content)
    
    # Remove lines that are clearly truncated (end with + or other operators in math)
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if re.search(r'\\\([^)]*[+\-*/]$', line.strip()):
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)
    
    # Fix incomplete inline math - close any unclosed math
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
    
    # Remove incomplete display math \[ that doesn't end with \]
    lines = content.split('\n')
    new_lines = []
    in_incomplete_math = False
    
    for i, line in enumerate(lines):
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
    
    # Convert ## headers to \section
    content = re.sub(r'^## (.+)$', r'\\section*{\1}', content, flags=re.MULTILINE)
    
    # Convert ### headers to \subsection
    content = re.sub(r'^### (.+)$', r'\\subsection*{\1}', content, flags=re.MULTILINE)
    
    # Convert **text** to \textbf{text}
    content = re.sub(r'\*\*([^*]+?)\*\*', r'\\textbf{\1}', content)
    
    # Fix patterns like \(d\)_-division_ - inline math followed by italic with hyphen
    content = re.sub(r'\\?\(([^)]+?)\\?\)_-([a-zA-Z]+)_', r'\\(\1\\)\\textit{-\2}', content)
    
    # Fix bullet points: <*> at start of line -> \item
    content = re.sub(r'^<\*\s*', r'\\item ', content, flags=re.MULTILINE)
    
    # Fix bullet points: * at start of line -> \item
    content = re.sub(r'^\*\s+', r'\\item ', content, flags=re.MULTILINE)
    
    # Wrap consecutive \item lines in itemize environment
    lines = content.split('\n')
    new_lines = []
    in_itemize = False
    
    for i, line in enumerate(lines):
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
    
    # Convert \(...\) inline math to $...$
    content = content.replace('\\(', '$')
    content = content.replace('\\)', '$')
    
    # Convert \[...\] display math to equation* environment
    content = content.replace('\\[', '\n\\begin{equation*}')
    content = content.replace('\\]', '\\end{equation*}\n')
    
    # Create full LaTeX document
    latex_doc = r'''% !TEX program = xelatex
\documentclass[11pt,a4paper]{article}

\usepackage{fontspec}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{enumitem}

\geometry{margin=1in}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.5em}
\setcounter{secnumdepth}{0}

\title{Converted Document}
\author{}
\date{}

\begin{document}

\maketitle

''' + content + r'''

\end{document}
'''
    
    if output_file is None:
        output_file = input_file.replace('.tex', '_full.tex')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_doc)
    
    print(f"Converted {input_file} -> {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 md2tex.py input.tex [-o output.tex]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = None
    
    if '-o' in sys.argv:
        output_file = sys.argv[sys.argv.index('-o') + 1]
    
    convert_mmd_to_latex(input_file, output_file)
