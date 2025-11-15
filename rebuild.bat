@echo off
chcp 65001 > nul
echo Building PDFXyViewer.exe...
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt > nul 2>&1

echo [2/3] Building executable with optimizations...
pyinstaller pdf_viewer.spec --clean --log-level=WARN

echo.
echo [3/3] Build complete!
echo.
echo Executable: dist\PDFXyViewer.exe
echo.
pause
