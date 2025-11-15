@echo off

REM フォルダ形式でビルド（依存関係問題の回避に最適）

echo Building PDF XY Viewer (Folder mode)...

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

REM PyInstallerでビルド（フォルダ形式）
echo Building executable...
pyinstaller --onedir --noconsole --name PDFXyViewer ^
    --collect-all pymupdf ^
    --copy-metadata pymupdf ^
    --collect-data pymupdf ^
    --hidden-import=fitz ^
    --hidden-import=pymupdf ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=PIL.Image ^
    --hidden-import=PIL.ImageTk ^
    pdf_viewer.py

echo Build complete! Application is in the 'dist\PDFXyViewer' folder.
echo Main executable: dist\PDFXyViewer\PDFXyViewer.exe
echo.
echo To distribute: Zip the entire 'dist\PDFXyViewer' folder
echo.

pause
