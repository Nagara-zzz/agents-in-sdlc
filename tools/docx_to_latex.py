#!/usr/bin/env python3
"""
简单的 docx -> XeLaTeX 转换器（基础版）
- 处理标题（Heading 1/2/3 或 中文标题样式）、段落、加粗与斜体、表格（输出 tabular）
- 不处理 Office 数学对象与复杂图形；这些需人工补入

用法: python tools\docx_to_latex.py "path\\to\\file.docx" latex_src\\main.tex
"""
import sys
from pathlib import Path
from docx import Document

LATEX_SPECIALS = {
    '\\': r'\\textbackslash{}',
    '&': r'\\&',
    '%': r'\\%',
    '$': r'\\$',
    '#': r'\\#',
    '_': r'\\_',
    '{': r'\\{',
    '}': r'\\}',
    '~': r'\\textasciitilde{}',
    '^': r'\\^{}',
    '"': r"\"{}",
}


def escape_latex(s: str) -> str:
    out = []
    for ch in s:
        if ch in LATEX_SPECIALS:
            out.append(LATEX_SPECIALS[ch])
        else:
            out.append(ch)
    return ''.join(out)


def run_paragraph(p):
    style = p.style.name if p.style is not None else ''
    text = ''
    for run in p.runs:
        t = escape_latex(run.text)
        if run.bold:
            t = '\\textbf{' + t + '}'
        if run.italic:
            t = '\\textit{' + t + '}'
        text += t
    if not text.strip():
        return '\\par\n'
    # Map heading styles
    lname = style.lower() if style else ''
    if 'heading' in lname or '标题' in lname or lname.startswith('heading'):
        # extract level number if present
        import re
        m = re.search(r'heading (\d+)', lname)
        if m:
            lvl = int(m.group(1))
        else:
            lvl = 1
        if lvl == 1:
            return '\\section{' + text + '}\n'
        elif lvl == 2:
            return '\\subsection{' + text + '}\n'
        elif lvl == 3:
            return '\\subsubsection{' + text + '}\n'
        else:
            return '\\paragraph{' + text + '}\n'
    # Normal paragraph
    return text + '\\par\n\n'


def table_to_latex(table):
    rows = len(table.rows)
    cols = len(table.columns)
    colspec = '|' + 'c|' * cols
    out = []
    out.append('\\begin{tabular}{' + colspec + '}')
    out.append('\\hline')
    for r in range(rows):
        cells = []
        for c in range(cols):
            txt = ''
            for p in table.rows[r].cells[c].paragraphs:
                for run in p.runs:
                    txt += escape_latex(run.text)
            cells.append(txt.replace('\n', ' '))
        out.append(' & '.join(cells) + ' \\ \\hline')
    out.append('\\end{tabular}\n')
    return '\\n'.join(out)


def convert(docx_path: Path):
    doc = Document(str(docx_path))
    body = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            body.append(run_paragraph(block))
        elif isinstance(block, Table):
            body.append(table_to_latex(block))
    return ''.join(body)


# Helpers from python-docx documentation to iterate paragraphs and tables in order
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    else:
        raise ValueError('未知父对象')
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            p = Paragraph(child, parent)
            yield p
        elif isinstance(child, CT_Tbl):
            t = Table(child, parent)
            yield t


def make_full_tex(body_text: str, title: str = '论文转换草稿'):
    pre = r"""\\documentclass[11pt]{article}
\\usepackage{fontspec}
\\usepackage{xeCJK}
\\setmainfont{Times New Roman}
\\setCJKmainfont{Noto Serif CJK SC}
\\usepackage{geometry}
\\geometry{a4paper,margin=1in}
\\usepackage{setspace}
\\onehalfspacing
\\usepackage{microtype}
\\usepackage{hyperref}
\\begin{document}
""" + '\\title{%s}\\maketitle\\n\n' % escape_latex(title)
    post = '\\end{document}\n'
    return pre + body_text + post


def main():
    if len(sys.argv) < 3:
        print('Usage: docx_to_latex.py input.docx output.tex', file=sys.stderr)
        sys.exit(2)
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    if not inp.exists():
        print('Input not found:', inp, file=sys.stderr)
        sys.exit(3)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = convert(inp)
    full = make_full_tex(body, title=inp.stem)
    out.write_text(full, encoding='utf-8')
    print('Wrote', out)

if __name__ == '__main__':
    main()
