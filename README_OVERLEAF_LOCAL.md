Overleaf 本地编译器（XeLaTeX + biber）

简介
----
本工具提供一个简单的命令行界面，用于在本地以 Overleaf 风格运行 LaTeX 编译：多轮 XeLaTeX + 可选 biber 支持。适合中文论文的快速本地编译与打包为可执行程序。

快速开始
--------
1. 确保已安装 TeX Live 或 MiKTeX，并且 xelatex/biber 在 PATH 中可用。
2. 安装本工具（可选 pip 本地安装）：
   python -m pip install .
3. 使用：
   python overleaf_local_cli.py path\to\main.tex --runs 3
   或（若已安装为命令）：
   overleaf-local path\to\project --engine xelatex

打包为 Windows 可执行
-----------------
运行 build_windows.bat（会调用 PyInstaller）后，dist\overleaf-local.exe 为单文件可执行。

注意事项
-----
- 本工具以源文件目录为工作目录进行编译；若源码中包含复杂的输入路径或外部包，请确保相对路径正确。
- 对于复杂模板或需要额外字体的中文论文，请预先在 TeX 系统中安装相应字体（例如 Noto Serif CJK / 思源宋体）。

扩展建议
-----
- 可集成文件监视以实现自动重编译
- 支持 -output-directory/-aux-directory 分离构建产物
- 支持更完善的日志分析与错误高亮

许可证: MIT

在 GitHub Actions 上编译（CI）
-------------------------
本仓库已包含一个 GitHub Actions workflow（.github/workflows/latex.yml），可在远程 runner 上安装 TeX Live（含 xelatex 与 biber）并生成 PDF 与日志作为 artifact。使用方法：

1) 在 GitHub 仓库页面：Actions -> 选择 "LaTeX build" -> 点击 "Run workflow"，可在表单中填写 "main_file"（例如 docs/main.tex 或 sample_main.tex），触发后等待运行完成，运行页面右侧的 Artifacts 可下载生成的 latex-output（包含 PDF 与日志）。

2) 使用 gh CLI（示例）：
   gh workflow run latex.yml --ref main --field main_file=sample_main.tex
   # 等待运行完成后查询并下载 artifact：
   gh run list --workflow=latex.yml
   gh run download <run-id> --name latex-output --dir ./latex-artifacts

注意：workflow 默认在仓库根目录寻找 main.tex，若你的主文件在子目录，请在触发时填写完整相对路径（例如 docs/thesis/main.tex）。

常见问题：
- 若编译失败，可下载并查看 .log 文件以定位错误；Actions 运行日志也会显示 xelatex/biber 的输出。
- 若模板需要额外字体或系统包，建议在 workflow 中调整 dante-ev/texlive-action 的 extra_packages 或在文件中使用 embed 字体。


