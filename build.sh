#!/bin/bash

# ビルドスクリプト

echo "Building PDF XY Viewer..."

# 仮想環境がなければ作成
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
source venv/bin/activate

# 依存パッケージをインストール
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# PyInstallerでビルド
echo "Building executable..."
pyinstaller pdf_viewer.spec --clean

echo "Build complete! Executable is in the 'dist' folder."
echo "File: dist/PDFXyViewer (Mac) or dist/PDFXyViewer.exe (Windows)"
