#!/usr/bin/env python3
"""
使用 CrossRef API 尝试基于条目 title 丰富 latex_src/refs.bib 的元数据（DOI、期刊、卷页、作者、年份）
生成 latex_src/refs_enriched.bib（若未找到匹配则保留原条目）

注意：CrossRef 对中文文献覆盖有限，脚本仅作自动尝试，需人工验证。
"""
import sys
import re
import urllib.parse
import urllib.request
import json
from pathlib import Path

BIB = Path('latex_src/refs.bib')
OUT = Path('latex_src/refs_enriched.bib')

if not BIB.exists():
    print('refs.bib not found')
    sys.exit(2)

bib_text = BIB.read_text(encoding='utf-8')
entries = re.split(r'(?=@)', bib_text)

headers = []
for e in entries:
    e = e.strip()
    if not e:
        continue
    m = re.match(r'@\w+\{([^,]+),', e)
    if not m:
        continue
    key = m.group(1)
    # extract title field
    t = re.search(r'title\s*=\s*\{([^}]*)\}', e, re.IGNORECASE)
    title = t.group(1).strip() if t else ''
    headers.append((key, title, e))

new_entries = []
for key, title, raw in headers:
    try:
        print('Searching CrossRef for:', title[:60])
    except Exception:
        print('Searching CrossRef for: (title hidden due to encoding)')
    if not title:
        new_entries.append(raw)
        continue
    q = urllib.parse.quote(title)
    url = f'https://api.crossref.org/works?query.title={q}&rows=1'
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.load(r)
    except Exception as ex:
        print('CrossRef request failed:', ex)
        new_entries.append(raw)
        continue
    items = data.get('message', {}).get('items', [])
    if not items:
        print('No items found')
        new_entries.append(raw)
        continue
    item = items[0]
    # crude title match
    found_title = ' '.join(item.get('title', []))
    if title.lower()[:20] not in found_title.lower()[:len(title)][:20]:
        # keep raw if poor match
        print('Poor title match, keeping original')
        new_entries.append(raw)
        continue
    # build bib entry
    doi = item.get('DOI','')
    year = ''
    if 'published-print' in item and 'date-parts' in item['published-print']:
        year = str(item['published-print']['date-parts'][0][0])
    elif 'published' in item and 'date-parts' in item['published']:
        year = str(item['published']['date-parts'][0][0])
    container = ' '.join(item.get('container-title', []))
    authors = []
    for a in item.get('author', []):
        name = ' '.join([a.get('given',''), a.get('family','')]).strip()
        if name:
            authors.append(name)
    pages = item.get('page','')
    volume = item.get('volume','')
    issue = item.get('issue','')
    if container:
        entry = f"@article{{{key},\n  title = {{{title}}},\n  author = {{{' and '.join(authors) if authors else 'Unknown'}}},\n  journal = {{{container}}},\n"
        if year:
            entry += f"  year = {{{year}}},\n"
        if volume:
            entry += f"  volume = {{{volume}}},\n"
        if issue:
            entry += f"  number = {{{issue}}},\n"
        if pages:
            entry += f"  pages = {{{pages}}},\n"
        if doi:
            entry += f"  doi = {{{doi}}},\n"
        entry += f"  note = {{Auto-enriched from CrossRef; original key {key}}},\n}}\n\n"
    else:
        entry = f"@misc{{{key},\n  title = {{{title}}},\n  author = {{{' and '.join(authors) if authors else 'Unknown'}}},\n"
        if year:
            entry += f"  year = {{{year}}},\n"
        if doi:
            entry += f"  doi = {{{doi}}},\n"
        entry += f"  note = {{Auto-enriched from CrossRef; original key {key}}},\n}}\n\n"
    new_entries.append(entry)

OUT.write_text(''.join(new_entries), encoding='utf-8')
print('Wrote', OUT)
print('注意：请人工核验 enriched bib 条目，特别是中文文献可能无匹配或匹配不准确。')
