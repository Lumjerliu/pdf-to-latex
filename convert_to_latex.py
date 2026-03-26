#!/usr/bin/env python3
"""Convert Mathpix Markdown to proper LaTeX document."""

import re

def convert_mmd_to_latex(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all control characters except newline, tab, carriage return
    cleaned = []
    for c in content:
        if c.isprintable() or c in '\n\t\r':
            cleaned.append(c)
    content = ''.join(cleaned)
    
    # Remove MISSING_PAGE markers
    content = re.sub(r'\[MISSING_PAGE[^\]]*\]', '', content)
    
    # Remove [0.5cm] markers
    content = content.replace('[0.5cm]', '\n\\medskip\n')
    
    # Remove incomplete display math
    lines = content.split('\n')
    new_lines = []
    in_incomplete_math = False
    
    for line in lines:
        if '\\[' in line and '\\]' not in line:
            in_incomplete_math = True
            continue
        if in_incomplete_math:
            if '\\]' in line or line.startswith('##'):
                in_incomplete_math = False
            continue
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Convert ## headers to \section
    content = re.sub(r'^## (.+)$', r'\\section*{\1}', content, flags=re.MULTILINE)
    
    # Convert ### headers to \subsection
    content = re.sub(r'^### (.+)$', r'\\subsection*{\1}', content, flags=re.MULTILINE)
    
    # Convert **text** to \textbf{text}
    content = re.sub(r'\*\*([^*]+?)\*\*', r'\\textbf{\1}', content)
    
    # Handle (_text_) pattern
    content = re.sub(r'\(_([^_]+?)_\)', r'(\\textit{\1})', content)
    content = re.sub(r'\(_([^_\)]+)\)_', r'(\\textit{\1})', content)
    
    # Handle _-word_ pattern
    content = re.sub(r'_(-[a-zA-Z]+?)_', r'\\textit{\1}', content)
    
    # Handle standalone _text_
    content = re.sub(r'(\s)_([a-zA-Z][^_]+?)_(\s)', r'\1\\textit{\2}\3', content)
    
    # Convert \(...\) to $...$ for inline math
    content = content.replace('\\(', '$')
    content = content.replace('\\)', '$')
    
    # Convert \[...\] to equation* environment
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

\begin{document}

''' + content + r'''

\end{document}
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_doc)
    
    print(f"Converted {input_file} -> {output_file}")

if __name__ == "__main__":
    convert_mmd_to_latex('output/IMO2024SL.tex', 'output/IMO2024SL_full.tex')
