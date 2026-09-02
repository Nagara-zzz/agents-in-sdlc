@echo off
REM 使用 PyInstaller 打包为单文件可执行（Windows）
REM 先创建 virtualenv 并安装本包：
REM python -m venv .venv
REM .venv\Scripts\activate
REM pip install --upgrade pip
REM pip install .

REM 安装 PyInstaller（若未安装）
pip install pyinstaller

REM 生成单文件可执行，名称 overleaf-local.exe
pyinstaller --noconfirm --onefile --name overleaf-local overleaf_local_cli.py

echo 打包完成。输出位于 dist\overleaf-local.exe
pause
