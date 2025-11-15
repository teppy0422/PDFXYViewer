@echo off

REM Windows用ビルドスクリプト

echo Building PDF XY Viewer...

REM 仮想環境がなければ作成
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM 仮想環境をアクティベート
call venv\Scripts\activate.bat

REM 依存パッケージをインストール
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM PyInstallerでビルド
echo Building executable...
pyinstaller pdf_viewer.spec --clean

echo Build complete! Executable is in the 'dist' folder.
echo File: dist\PDFXyViewer.exe

pause
