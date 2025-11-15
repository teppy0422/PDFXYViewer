@echo off

REM 代替ビルドスクリプト（PyMuPDF問題の回避用）

echo Building PDF XY Viewer (Alternative method)...

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

REM 古いビルドをクリーンアップ
echo Cleaning old builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM PyInstallerでビルド（--collect-allでPyMuPDFをすべて含める）
echo Building executable...
pyinstaller --onefile --console --name PDFXyViewer ^
    --collect-all pymupdf ^
    --copy-metadata pymupdf ^
    --collect-data pymupdf ^
    --hidden-import=fitz ^
    --hidden-import=pymupdf ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    pdf_viewer.py

echo Build complete! Executable is in the 'dist' folder.
echo File: dist\PDFXyViewer.exe

pause
