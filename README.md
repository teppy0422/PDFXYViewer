# PDF XY Viewer

PDF ファイルを開いて、マウスの XY 座標をリアルタイムで表示するビューアーアプリです。

## 機能

- PDF ファイルの表示
- マウス座標のリアルタイム表示（左下のステータスバー）
- 右クリックで座標をクリップボードにコピー
- ページナビゲーション（前へ/次へ）
- ズーム機能（+/-ボタン）
- キーボードショートカット対応

## 開発環境のセットアップ

### 必要なもの

- Python 3.8 以上
- pip

### セットアップ手順

1. リポジトリをクローン（またはダウンロード）

2. 仮想環境を作成（推奨）

```bash
python3 -m venv venv
```

3. 仮想環境をアクティベート

**Mac/Linux:**

```bash
source venv/bin/activate
```

**Windows:**

```bash
venv\Scripts\activate.bat
```

4. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

## 開発中の実行

```bash
python pdf_viewer.py
```

## ビルド（実行ファイル作成）

### Mac/Linux の場合

```bash
chmod +x build.sh
./build.sh
```

### Windows の場合

**初回ビルド時（仮想環境から作成）:**

```bash
build.bat
```

**2回目以降のビルド（環境が既にある場合）:**

```bash
rebuild.bat
```

ビルドが完了すると、`dist`フォルダに実行ファイルが生成されます。

- **Mac/Linux:** `dist/PDFXyViewer`
- **Windows:** `dist/PDFXyViewer.exe`

### 配布用の ZIP ファイル作成

Windows でビルドした後：

```bash
# distフォルダに移動
cd dist

# ZIPファイルを作成
# Windows PowerShell:
Compress-Archive -Path PDFXyViewer.exe -DestinationPath PDFXyViewer.zip

# または、7-Zipなどを使用
7z a -tzip PDFXyViewer.zip PDFXyViewer.exe
```

圧縮後のファイルサイズは **約 20-40MB** になります。

## 使い方

### 基本操作

1. アプリを起動
2. `File` → `Open PDF` で PDF ファイルを開く
3. マウスを動かすと、左下に座標が表示されます
4. 右クリックすると、その座標がクリップボードにコピーされます

### キーボードショートカット

- `Ctrl+O` (Mac: `Cmd+O`): PDF を開く
- `←` (左矢印): 前のページ
- `→` (右矢印): 次のページ

### ボタン

- `◀ Previous`: 前のページへ
- `Next ▶`: 次のページへ
- `+`: ズームイン
- `-`: ズームアウト

## トラブルシューティング

### Mac で開発時に pyperclip がエラーを出す場合

```bash
# pbcopyが使えるか確認（Macでは標準で使えるはず）
which pbcopy
```

### Windows でクリップボードが動作しない場合

pyperclip は自動的に適切なクリップボードメカニズムを選択しますが、問題がある場合は以下を確認：

1. Windows 10 以上であることを確認
2. 管理者権限で実行してみる

## ライセンス

MIT License

## 開発者向け情報

### 使用ライブラリ

- **PyMuPDF (fitz)**: PDF レンダリング
- **Pillow**: 画像処理
- **pyperclip**: クリップボード操作
- **tkinter**: GUI（Python 標準ライブラリ）

### ファイル構成

```
pdfXyViewer/
├── pdf_viewer.py          # メインアプリケーション
├── pdf_viewer.spec        # PyInstaller設定ファイル
├── requirements.txt       # 依存パッケージリスト
├── build.sh              # Mac/Linux用ビルドスクリプト
├── build.bat             # Windows用初回ビルドスクリプト
├── rebuild.bat           # Windows用クイックビルドスクリプト
├── hippo_019_cir.ico     # アプリケーションアイコン
└── README.md             # このファイル
```

### ビルドサイズの最適化

現在の設定では以下の最適化が施されています：

- `--onefile`: 単一実行ファイルとして出力
- `upx=True`: UPX 圧縮を有効化（さらなるサイズ削減）
- `console=False`: コンソールウィンドウを非表示

さらにサイズを削減したい場合：

1. 不要なライブラリを除外する
2. `excludes`パラメータで使用しないモジュールを指定
3. Python 3.11 以上を使用（バイナリサイズが小さい）

## VS Code での開発

### 推奨拡張機能

- Python (Microsoft)
- Pylance
- Python Debugger

### デバッグ設定 (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```
