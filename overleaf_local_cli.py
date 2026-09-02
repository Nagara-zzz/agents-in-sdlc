#!/usr/bin/env python3
"""
简单的本地 LaTeX 编译器（Overleaf 风格的命令行工具，支持 XeLaTeX + biber 多轮编译）
用法示例：
  python overleaf_local_cli.py path\to\project\main.tex --runs 3
  python overleaf_local_cli.py path\to\project --engine xelatex

设计目标：在用户机器上以最小依赖实现可重复的多轮编译流程，适合中文论文（XeLaTeX 默认）。
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def check_tool(name):
    return shutil.which(name) is not None


def run(cmd, cwd, logfile):
    logfile.write(f"\n--- {datetime.now().isoformat()} RUN: {' '.join(cmd)} (cwd={cwd})\n")
    logfile.flush()
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logfile.write(proc.stdout)
    logfile.flush()
    return proc.returncode


def find_main_tex(path: Path):
    if path.is_file():
        if path.suffix.lower() == '.tex':
            return path.resolve()
        else:
            raise FileNotFoundError('指定的文件不是 .tex 文件')
    if path.is_dir():
        candidates = list(path.glob('*.tex'))
        if not candidates:
            raise FileNotFoundError('目录中找不到 .tex 文件')
        # 优先 main.tex
        for c in candidates:
            if c.name.lower() == 'main.tex':
                return c.resolve()
        # 否则取第一个
        return candidates[0].resolve()
    raise FileNotFoundError('找不到指定路径')


def main():
    p = argparse.ArgumentParser(description='本地 XeLaTeX/biber 编译工具')
    p.add_argument('source', help='主 .tex 文件或包含 .tex 的目录')
    p.add_argument('--engine', default='xelatex', choices=['xelatex', 'pdflatex', 'lualatex'], help='TeX 引擎（默认 xelatex）')
    p.add_argument('--runs', type=int, default=3, help='XeLaTeX 运行次数（默认 3）')
    p.add_argument('--out', help='输出目录（默认与源同目录）')
    p.add_argument('--clean', action='store_true', help='完成后清理中间文件（.aux/.log/.bbl 等）')
    args = p.parse_args()

    src = Path(args.source)
    try:
        main_tex = find_main_tex(src)
    except FileNotFoundError as e:
        print('错误：', e, file=sys.stderr)
        sys.exit(2)

    srcdir = main_tex.parent
    basename = main_tex.stem
    outdir = Path(args.out) if args.out else srcdir
    outdir = outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # 检查工具
    if not check_tool(args.engine):
        print(f'错误：没有在 PATH 中找到 {args.engine}。请安装 TeX Live 或 MiKTeX 并确保 {args.engine} 可用。', file=sys.stderr)
        sys.exit(3)
    has_biber = check_tool('biber')

    log_path = outdir / f'{basename}_compile.log'
    with open(log_path, 'a', encoding='utf-8') as logfile:
        logfile.write(f'Compile session start: {datetime.now().isoformat()}\n')
        logfile.write(f'Main tex: {main_tex}\nEngine: {args.engine}\nRuns: {args.runs}\nOutdir: {outdir}\n')

        # Run multiple xelatex runs; run biber if .bib exists
        bibs = list(srcdir.glob('*.bib'))
        ran_biber = False
        # First N-1 runs
        for i in range(args.runs):
            rc = run([args.engine, '-interaction=nonstopmode', '-halt-on-error', main_tex.name], cwd=srcdir, logfile=logfile)
            if rc != 0:
                print(f'LaTeX 编译失败（轮次 {i+1}），参见日志：{log_path}', file=sys.stderr)
                sys.exit(rc)
            # 在第一次或中间轮次检测并运行 biber（若存在 .bib）
            if bibs and has_biber and not ran_biber:
                # biber 操作通常基于主文件名
                rc_b = run(['biber', basename], cwd=srcdir, logfile=logfile)
                if rc_b != 0:
                    print(f'biber 运行失败，参见日志：{log_path}', file=sys.stderr)
                    sys.exit(rc_b)
                ran_biber = True

        # 最后再运行一次 engine 以稳定交叉引用
        rc = run([args.engine, '-interaction=nonstopmode', '-halt-on-error', main_tex.name], cwd=srcdir, logfile=logfile)
        if rc != 0:
            print('最终 LaTeX 编译失败，参见日志', file=sys.stderr)
            sys.exit(rc)

        # 将生成的 PDF 移动到 outdir（若不同）
        generated_pdf = srcdir / f'{basename}.pdf'
        if generated_pdf.exists():
            if outdir != srcdir:
                target_pdf = outdir / generated_pdf.name
                shutil.move(str(generated_pdf), str(target_pdf))
                logfile.write(f'Moved PDF to {target_pdf}\n')
                print(f'生成成功：{target_pdf}')
            else:
                print(f'生成成功：{generated_pdf}')
        else:
            print('未找到生成的 PDF，可能编译成功但输出位置不同，检查日志：', log_path, file=sys.stderr)
            sys.exit(4)

        # 可选清理
        if args.clean:
            patterns = ['*.aux','*.log','*.out','*.bbl','*.bcf','*.blg','*.run.xml','*.toc']
            for pat in patterns:
                for f in srcdir.glob(pat):
                    try:
                        f.unlink()
                        logfile.write(f'Removed {f}\n')
                    except Exception as ex:
                        logfile.write(f'Failed to remove {f}: {ex}\n')

        logfile.write('Compile session end.\n')


if __name__ == '__main__':
    main()
