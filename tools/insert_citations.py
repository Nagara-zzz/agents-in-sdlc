#!/usr/bin/env python3
"""
按 refs.bib 条目顺序，将 latex_src/main.tex 中的空方括号引用 [] 按出现顺序替换为 \cite{key}
用法: python tools\insert_citations.py latex_src\main.tex latex_src\refs.bib
"""
import sys
import re
from pathlib import Path

if len(sys.argv) < 3:
    print('Usage: insert_citations.py MAIN_TEX REFS_BIB')
    sys.exit(2)

main_tex = Path(sys.argv[1])
refs_bib = Path(sys.argv[2])
if not main_tex.exists() or not refs_bib.exists():
    print('Files not found')
    sys.exit(3)

text = main_tex.read_text(encoding='utf-8')
refs = refs_bib.read_text(encoding='utf-8')
keys = re.findall(r'@\w+\{([^,]+),', refs)
if not keys:
    print('No bib keys found')
    sys.exit(4)

key_iter = iter(keys)

# replace only empty brackets like [] or [   ]
pattern = re.compile(r"\[\s*\]")
count = 0

def repl(m):
    global count
    try:
        k = next(key_iter)
    except StopIteration:
        k = keys[-1]
    count += 1
    return f'[\\cite{{{k}}}]'

new_text, n = pattern.subn(repl, text)
main_tex.write_text(new_text, encoding='utf-8')
print(f'Replaced {n} empty bracket occurrences with \cite{{}} entries')
