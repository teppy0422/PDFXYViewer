import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageOps, ImageDraw
import pyperclip
import io
import sys
import os
import ctypes
import webbrowser

# Windows高DPI対応（アプリ全体をシャープに表示）
try:
    if sys.platform == 'win32':
        # Windows 8.1以降
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        # Windows Vista/7
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass


class PDFViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF XY Viewer")
        self.root.geometry("1000x800")

        # アイコンを設定
        self.set_window_icon()

        self.pdf_document = None
        self.current_page = 0
        self.zoom = 1.5  # ズームレベル（高解像度で表示）
        self.coord_scale = tk.DoubleVar(value=1.0)  # 座標表示の倍率
        self.image_file = None  # 画像ファイル用（PNG/JPG）
        self.is_image_mode = False  # 画像モードかどうか
        self.cached_image = None  # 画像ファイルのキャッシュ（元画像）
        self.render_timer = None  # レンダリング遅延用タイマー
        self.invert_colors = False  # グレースケール反転フラグ

        # パン機能用
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False

        # メニューバー
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)

        # 使い方メニュー
        menubar.add_command(label="How to Use", command=self.show_usage)

        # About Thisメニュー
        menubar.add_command(label="About This", command=self.show_about)

        # ツールバー
        toolbar = tk.Frame(root, bg="lightgray")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.prev_btn = tk.Button(toolbar, text="◀ Previous", command=self.prev_page, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.page_label = tk.Label(toolbar, text="No PDF loaded", bg="lightgray")
        self.page_label.pack(side=tk.LEFT, padx=20)

        self.next_btn = tk.Button(toolbar, text="Next ▶", command=self.next_page, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # マーカークリアボタン
        self.clear_markers_btn = tk.Button(toolbar, text="Clear Markers", command=self.clear_markers, state=tk.DISABLED)
        self.clear_markers_btn.pack(side=tk.LEFT, padx=(20, 5))

        # グレースケール反転ボタン
        self.invert_btn = tk.Button(toolbar, text="⚫⚪ Invert", command=self.toggle_invert, state=tk.DISABLED)
        self.invert_btn.pack(side=tk.LEFT, padx=(5, 5))

        # 座標倍率設定
        scale_label = tk.Label(toolbar, text="Coord Scale:", bg="lightgray")
        scale_label.pack(side=tk.LEFT, padx=(20, 5))

        scale_options = [0.0001,0.005,0.001,0.005,0.01,0.05, 0.1, 0.5, 1.0, 2.0]
        self.scale_dropdown = tk.OptionMenu(toolbar, self.coord_scale, *scale_options)
        self.scale_dropdown.config(width=5)
        self.scale_dropdown.pack(side=tk.LEFT, padx=2)

        # キャンバス（PDF表示エリア）
        canvas_frame = tk.Frame(root)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="gray")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # スクロールバー
        scrollbar_y = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # ステータスバー（座標表示）
        self.status_bar = tk.Label(root, text="0_0", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # イベントバインディング
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)  # 左クリックで座標コピー
        self.canvas.bind("<Button-3>", self.on_pan_start)  # 右クリックでパン開始（Windows）
        self.canvas.bind("<Button-2>", self.on_pan_start)  # Macでは<Button-2>が右クリック
        self.canvas.bind("<ButtonRelease-3>", self.on_pan_end)  # 右クリック解放
        self.canvas.bind("<ButtonRelease-2>", self.on_pan_end)  # Mac用
        self.canvas.bind("<B3-Motion>", self.on_pan_move)  # 右クリックドラッグ（Windows）
        self.canvas.bind("<B2-Motion>", self.on_pan_move)  # Mac用
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # マウスホイールでY方向スクロール
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)  # Shift+ホイールでX方向
        self.canvas.bind("<Control-MouseWheel>", self.on_ctrl_mousewheel)  # Ctrl+ホイールでズーム

        # キーボードショートカット
        self.root.bind("<Left>", lambda e: self.prev_page())
        self.root.bind("<Right>", lambda e: self.next_page())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Command-o>", lambda e: self.open_file())  # Mac用

        self.photo_image = None  # 画像の参照を保持
        self.placeholder_image = None  # プレースホルダー画像の参照を保持
        self.marker_images = []  # マーカー画像の参照を保持
        self.marker_positions = []  # マーカーの座標リスト

        # プレースホルダー画像を読み込む
        self.load_placeholder_image()

        # ドラッグアンドドロップのサポート
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # キャンバスのリサイズイベントをバインド
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        # 初期状態でプレースホルダー画像を表示（少し遅延して実行）
        self.root.after(100, self.display_placeholder)

    def set_window_icon(self):
        """ウィンドウアイコンを設定"""
        try:
            # 実行ファイルの場所を取得（PyInstallerでビルドした場合に対応）
            if getattr(sys, 'frozen', False):
                # PyInstallerでビルドされた場合
                base_path = sys._MEIPASS
            else:
                # 通常のPythonスクリプトとして実行された場合
                base_path = os.path.dirname(os.path.abspath(__file__))

            icon_path = os.path.join(base_path, 'hippo_019_cir.ico')

            # アイコンを設定
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not set icon: {str(e)}")

    def on_drop(self, event):
        """ドラッグアンドドロップされたファイルを開く"""
        files = self.root.tk.splitlist(event.data)
        if files:
            file_path = files[0]
            # Windowsのパスからブレース{}を削除
            file_path = file_path.strip('{}')
            ext = file_path.lower()
            if ext.endswith('.pdf') or ext.endswith('.png') or ext.endswith('.jpg') or ext.endswith('.jpeg'):
                self.load_file(file_path)
            else:
                messagebox.showwarning("Warning", "Please drop a PDF, PNG, or JPG file.")

    def load_placeholder_image(self):
        """プレースホルダー画像（hippo_019.png）を読み込む"""
        try:
            # 実行ファイルの場所を取得（PyInstallerでビルドした場合に対応）
            if getattr(sys, 'frozen', False):
                # PyInstallerでビルドされた場合
                base_path = sys._MEIPASS
            else:
                # 通常のPythonスクリプトとして実行された場合
                base_path = os.path.dirname(os.path.abspath(__file__))

            image_path = os.path.join(base_path, 'hippo_019.png')

            # 画像を読み込み
            img = Image.open(image_path)

            # パレット画像の場合、警告を避けるために明示的にRGBAに変換
            if img.mode == 'P':
                img = img.convert('RGBA')
            elif img.mode != 'RGBA':
                img = img.convert('RGBA')

            # アスペクト比を維持したまま固定サイズ（最大300x300）に収める
            max_size = (300, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 透過処理（アルファ値を50%に設定）
            alpha = img.split()[3]  # アルファチャンネルを取得
            alpha = alpha.point(lambda p: int(p * 0.3))  # 30%透過
            img.putalpha(alpha)

            # PhotoImageに変換
            self.placeholder_image = ImageTk.PhotoImage(img)

        except Exception as e:
            print(f"Warning: Could not load placeholder image: {str(e)}")
            self.placeholder_image = None

    def on_canvas_configure(self, event):
        """キャンバスがリサイズされた時の処理"""
        # ファイルが開かれていない場合のみプレースホルダーを再描画
        if not self.pdf_document and not self.image_file:
            self.display_placeholder()

    def display_placeholder(self):
        """プレースホルダー画像を画面中央に表示"""
        if not self.placeholder_image:
            return

        # キャンバスをクリア
        self.canvas.delete("all")

        # キャンバスの実際のサイズを取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # サイズが正しく取得できない場合はスキップ
        if canvas_width <= 1 or canvas_height <= 1:
            return

        # 画像を中央に配置
        x = canvas_width // 2
        y = canvas_height // 2

        self.canvas.create_image(x, y, image=self.placeholder_image)

        # スクロール領域をリセット
        self.canvas.config(scrollregion=(0, 0, 0, 0))

    def open_file(self):
        """ファイルを開く（ダイアログ表示）"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("Supported files", "*.pdf;*.png;*.jpg;*.jpeg"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png;*.jpg;*.jpeg"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        """ファイルを読み込む（PDF/PNG/JPG対応）"""
        try:
            ext = file_path.lower()

            # 既存のファイルをクローズ
            if self.pdf_document:
                self.pdf_document.close()
                self.pdf_document = None
            self.image_file = None
            self.cached_image = None  # キャッシュをクリア
            self.marker_positions = []  # マーカーをクリア

            # ファイルの種類で分岐
            if ext.endswith('.pdf'):
                # PDFモード
                self.is_image_mode = False
                self.pdf_document = fitz.open(file_path)
                self.current_page = 0
                self.display_page()

                # ページナビゲーションボタンを有効化
                self.prev_btn.config(state=tk.NORMAL)
                self.next_btn.config(state=tk.NORMAL)

            elif ext.endswith('.png') or ext.endswith('.jpg') or ext.endswith('.jpeg'):
                # 画像モード
                self.is_image_mode = True
                self.image_file = file_path
                self.current_page = 0

                # 画像を読み込んでキャッシュ
                self.cached_image = Image.open(file_path)
                if self.cached_image.mode == 'P':
                    self.cached_image = self.cached_image.convert('RGBA')
                elif self.cached_image.mode != 'RGB' and self.cached_image.mode != 'RGBA':
                    self.cached_image = self.cached_image.convert('RGB')

                self.display_page()

                # ページナビゲーションボタンを無効化（画像は1ページのみ）
                self.prev_btn.config(state=tk.DISABLED)
                self.next_btn.config(state=tk.DISABLED)

            # 共通ボタンを有効化
            self.clear_markers_btn.config(state=tk.NORMAL)
            self.invert_btn.config(state=tk.NORMAL)

            # ファイル名を取得（WindowsとUnix両対応）
            filename = os.path.basename(file_path)
            self.root.title(f"PDF XY Viewer - {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def display_page(self, quality='high'):
        """現在のページを表示（PDF/画像対応）

        Args:
            quality: 'low' (高速・低品質) or 'high' (低速・高品質)
        """
        if not self.pdf_document and not self.image_file:
            return

        try:
            # マーカー画像の参照をクリア（座標は保持）
            self.marker_images = []

            if self.is_image_mode:
                # 画像モード（キャッシュから取得）
                if self.cached_image is None:
                    return

                # ズームを適用
                original_size = self.cached_image.size
                new_size = (int(original_size[0] * self.zoom), int(original_size[1] * self.zoom))

                # 品質に応じてリサンプリング方法を切り替え
                if quality == 'low':
                    img = self.cached_image.resize(new_size, Image.Resampling.BILINEAR)
                else:
                    img = self.cached_image.resize(new_size, Image.Resampling.LANCZOS)

                # 座標スケールを自動調整（X座標が3桁以内になるように）
                self.auto_adjust_coord_scale(new_size[0])

                # グレースケール反転処理
                if self.invert_colors:
                    img = img.convert('L')  # グレースケールに変換
                    img = ImageOps.invert(img)  # 反転

                # PIL ImageをTkinter PhotoImageに変換
                self.photo_image = ImageTk.PhotoImage(img)

                # ページ情報を更新（画像は1ページのみ）
                self.page_label.config(text="Image")

            else:
                # PDFモード
                page = self.pdf_document[self.current_page]

                # 品質に応じてレンダリング解像度を変更
                if quality == 'low':
                    # 低品質モード: 解像度を70%に下げて高速化
                    zoom_factor = self.zoom * 0.7
                else:
                    # 高品質モード: 通常の解像度
                    zoom_factor = self.zoom

                # ページをPixmapにレンダリング（ズームを適用）
                mat = fitz.Matrix(zoom_factor, zoom_factor)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # 座標スケールを自動調整（X座標が3桁以内になるように）
                self.auto_adjust_coord_scale(int(pix.width / zoom_factor * self.zoom))

                # PixmapをPIL Imageに変換
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))

                # 低品質モードでレンダリングした場合、実際のズームサイズにリサイズ
                if quality == 'low':
                    target_size = (int(pix.width / 0.7), int(pix.height / 0.7))
                    img = img.resize(target_size, Image.Resampling.BILINEAR)

                # グレースケール反転処理
                if self.invert_colors:
                    img = img.convert('L')  # グレースケールに変換
                    img = ImageOps.invert(img)  # 反転

                # PIL ImageをTkinter PhotoImageに変換
                self.photo_image = ImageTk.PhotoImage(img)

                # ページ情報を更新
                self.page_label.config(text=f"Page {self.current_page + 1} / {len(self.pdf_document)}")

                # ページナビゲーションボタンの状態を更新
                self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
                self.next_btn.config(state=tk.NORMAL if self.current_page < len(self.pdf_document) - 1 else tk.DISABLED)

            # キャンバスをクリア
            self.canvas.delete("all")

            # キャンバスに画像を表示
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

            # スクロール領域を更新
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            # マーカーを再描画
            for x, y in self.marker_positions:
                self._draw_marker_at(x, y)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to display: {str(e)}")

    def auto_adjust_coord_scale(self, width):
        """X座標が3桁以内になるようにスケールを自動調整"""
        # 利用可能なスケールオプション
        scale_options = [0.0001,0.005,0.001,0.005,0.01,0.05, 0.1, 0.5, 1.0, 2.0]

        # X座標が999以下になる最大のスケールを見つける
        best_scale = 1  # デフォルト最小値
        for scale in scale_options:
            if width * scale <= 999:
                best_scale = scale
            else:
                break

        # スケールを設定
        self.coord_scale.set(best_scale)

    def prev_page(self):
        """前のページに移動"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            # ページ移動時はマーカーをクリア
            self.marker_positions = []
            self.display_page()

    def next_page(self):
        """次のページに移動"""
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            # ページ移動時はマーカーをクリア
            self.marker_positions = []
            self.display_page()

    def clear_markers(self):
        """赤丸マーカーを全てクリア"""
        # マーカーをクリア
        self.marker_images = []
        self.marker_positions = []

        # 現在のページを再描画
        if self.pdf_document or self.image_file:
            self.display_page()

    def toggle_invert(self):
        """グレースケール反転を切り替え"""
        self.invert_colors = not self.invert_colors

        # ボタンの表示を更新
        if self.invert_colors:
            self.invert_btn.config(text="⚪⚫ Normal")
        else:
            self.invert_btn.config(text="⚫⚪ Invert")

        # ページを再描画
        self.display_page()

    def on_mouse_move(self, event):
        """マウス移動時の座標を表示"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # パン中でなければ座標を表示
        if not self.is_panning:
            # 倍率を適用
            scale = self.coord_scale.get()
            scaled_x = x * scale
            scaled_y = y * scale
            self.status_bar.config(text=f"{int(scaled_x)}_{int(scaled_y)}")

    def on_left_click(self, event):
        """左クリック時に座標をクリップボードにコピー"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # 倍率を適用
        scale = self.coord_scale.get()
        scaled_x = x * scale
        scaled_y = y * scale
        coord_text = f"{int(scaled_x)}_{int(scaled_y)}"

        try:
            pyperclip.copy(coord_text)
            # 一時的にステータスバーにコピー完了を表示
            self.status_bar.config(text=f"{coord_text} - Copied!", fg="green")
            self.root.after(2000, lambda: self.status_bar.config(text=coord_text, fg="black"))

            # クリック位置に赤い丸を描画
            self.draw_marker(x, y)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {str(e)}")

    def draw_marker(self, x, y):
        """クリック位置に赤い丸マーカーを描画

        Args:
            x, y: キャンバス上の絶対座標
        """
        # 座標を正規化して保存（元画像の座標系に変換）
        normalized_x = x / self.zoom
        normalized_y = y / self.zoom
        self.marker_positions.append((normalized_x, normalized_y))

        # マーカーを描画
        self._draw_marker_at(normalized_x, normalized_y)

    def _draw_marker_at(self, normalized_x, normalized_y):
        """指定座標にマーカーを描画（内部用）

        Args:
            normalized_x, normalized_y: 正規化座標（元画像の座標系）
        """
        # 現在のズーム倍率を適用して実座標に変換
        x = normalized_x * self.zoom
        y = normalized_y * self.zoom

        # PILで半透明の赤い円を作成
        size = 20
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # 透明な背景
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size-1, size-1], fill=(255, 0, 0, 128))  # 赤色、50%透過

        # PhotoImageに変換
        marker_img = ImageTk.PhotoImage(img)

        # キャンバスに配置（中心座標で配置）
        self.canvas.create_image(x, y, image=marker_img)

        # 画像の参照を保持（ガベージコレクションを防ぐ）
        self.marker_images.append(marker_img)

    def on_pan_start(self, event):
        """パン開始（右クリック押下）"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.config(cursor="hand2")  # カーソルを手のアイコンに変更

    def on_pan_move(self, event):
        """パン中の移動（右クリックドラッグ）"""
        if self.is_panning:
            # 移動量を計算
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y

            # キャンバスをスクロール
            self.canvas.xview_scroll(int(-dx / 10), "units")
            self.canvas.yview_scroll(int(-dy / 10), "units")

            # 開始位置を更新
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def on_pan_end(self, event):
        """パン終了（右クリック解放）"""
        self.is_panning = False
        self.canvas.config(cursor="")  # カーソルを元に戻す

    def on_mousewheel(self, event):
        """マウスホイールでY方向にスクロール"""
        # Windowsでは event.delta が 120/-120
        # 正の値で上スクロール（上に移動 = Y減少）、負の値で下スクロール（下に移動 = Y増加）
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")

    def on_shift_mousewheel(self, event):
        """Shift+マウスホイールでX方向にスクロール"""
        if event.delta > 0:
            self.canvas.xview_scroll(-1, "units")
        else:
            self.canvas.xview_scroll(1, "units")

    def on_ctrl_mousewheel(self, event):
        """Ctrl+マウスホイールでズーム（段階的レンダリング + 遅延実行）"""
        if not self.pdf_document and not self.image_file:
            return

        # 前回のズーム値を保存
        old_zoom = self.zoom

        if event.delta > 0:
            # ズームイン
            self.zoom *= 1.1
        else:
            # ズームアウト
            self.zoom /= 1.1

        # ズーム倍率の制限（0.1倍～10倍）
        self.zoom = max(0.1, min(10.0, self.zoom))

        # ズーム値が変わらない場合は処理しない
        if abs(self.zoom - old_zoom) < 0.001:
            return

        # 既存の高品質レンダリングタイマーをキャンセル
        if self.render_timer is not None:
            self.root.after_cancel(self.render_timer)
            self.render_timer = None

        # カーソルを待機状態に変更
        self.canvas.config(cursor="watch")
        self.root.config(cursor="watch")

        # 即座に低品質プレビューを表示
        self.display_page(quality='low')

        # ズーム倍率を一時的に表示
        zoom_percent = int(self.zoom * 100)
        self.status_bar.config(text=f"Zoom: {zoom_percent}%", fg="blue")

        # 300ms後に高品質レンダリングを実行
        self.render_timer = self.root.after(300, self._render_high_quality)

    def _render_high_quality(self):
        """高品質レンダリングを実行（遅延後）"""
        self.render_timer = None
        try:
            self.display_page(quality='high')
        finally:
            # カーソルを元に戻す
            self.canvas.config(cursor="")
            self.root.config(cursor="")
            # ステータスバーの色を元に戻す
            self.root.after(1500, lambda: self.status_bar.config(fg="black"))

    def center_window(self, window, width, height):
        """ウィンドウをメインウィンドウの中央に配置"""
        # メインウィンドウの位置とサイズを取得
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # 中央座標を計算
        x = main_x + (main_width - width) // 2
        y = main_y + (main_height - height) // 2

        # ウィンドウの位置とサイズを設定
        window.geometry(f"{width}x{height}+{x}+{y}")

    def create_usage_card(self, parent, title, items):
        """使い方カードを作成"""
        # カード全体のフレーム
        card = tk.Frame(parent, bg="#f5f5f5", relief=tk.FLAT, bd=0)
        card.pack(fill=tk.X, padx=20, pady=8)

        # 内側のパディング用フレーム
        inner_frame = tk.Frame(card, bg="#f5f5f5")
        inner_frame.pack(fill=tk.BOTH, padx=15, pady=15)

        # タイトル
        title_label = tk.Label(inner_frame, text=title, font=("Meiryo UI", 12, "bold"),
                              bg="#f5f5f5", fg="#2c3e50", anchor=tk.W)
        title_label.pack(fill=tk.X, pady=(0, 10))

        # 項目リスト
        for item in items:
            if item:  # 空文字列でない場合
                item_label = tk.Label(inner_frame, text=f"• {item}", font=("Meiryo UI", 10),
                                     bg="#f5f5f5", fg="#34495e", anchor=tk.W, justify=tk.LEFT)
                item_label.pack(fill=tk.X, pady=2)
            else:  # 空行の場合
                tk.Frame(inner_frame, bg="#f5f5f5", height=5).pack()

    def show_usage(self):
        """使い方をモーダル表示"""
        usage_window = tk.Toplevel(self.root)
        usage_window.title("How to Use")
        usage_window.resizable(False, False)
        usage_window.transient(self.root)
        usage_window.grab_set()

        # ウィンドウを中央に配置
        self.center_window(usage_window, 600, 600)

        # モーダルにもアイコンを設定
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'hippo_019_cir.ico')
            if os.path.exists(icon_path):
                usage_window.iconbitmap(icon_path)
        except:
            pass

        # スクロール可能なメインフレーム
        main_frame = tk.Frame(usage_window, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # キャンバスとスクロールバー
        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # マウスホイールでスクロール
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # ウィンドウが閉じられた時にバインドを解除
        def on_close():
            usage_window.unbind("<MouseWheel>")
            usage_window.destroy()

        usage_window.protocol("WM_DELETE_WINDOW", on_close)
        usage_window.bind("<MouseWheel>", on_mousewheel)

        # パディング用の上部スペース
        tk.Frame(scrollable_frame, bg="white", height=20).pack()

        # カード1: 対応ファイル
        self.create_usage_card(scrollable_frame, "📄 対応ファイル", [
            "PDF, PNG, JPG, JPEG"
        ])

        # カード2: マウス操作
        self.create_usage_card(scrollable_frame, "🖱 マウス操作", [
            "左クリック: 座標をクリップボードにコピー（形式: 10_22）",
            "右クリック+ドラッグ: 画面をパン（移動）",
            "マウスホイール: 縦スクロール",
            "Shift+ホイール: 横スクロール",
            "Ctrl+ホイール: ズームイン/アウト"
        ])

        # カード4: 座標倍率
        self.create_usage_card(scrollable_frame, "📐 座標倍率（Coord Scale）", [
            "ツールバーで座標の表示倍率を変更できます",
            "",
            "0.0001～2.0: 実座標の 1/10000倍から2倍 で表示",
            "",
            "※PDFの横幅に応じて自動的に切り替わります"
        ])

        # パディング用の下部スペース
        tk.Frame(scrollable_frame, bg="white", height=10).pack()

        # 閉じるボタン
        close_btn = tk.Button(usage_window, text="閉じる", command=on_close, width=10, font=("Meiryo UI", 9))
        close_btn.pack(pady=10)

    def show_about(self):
        """About情報をモーダル表示"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About This Application")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()

        # ウィンドウを中央に配置
        self.center_window(about_window, 500, 500)

        # モーダルにもアイコンを設定
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'hippo_019_cir.ico')
            if os.path.exists(icon_path):
                about_window.iconbitmap(icon_path)
        except:
            pass

        # 内容
        content_frame = tk.Frame(about_window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # アプリ名
        app_name = tk.Label(content_frame, text="PDF XY Viewer", font=("Meiryo UI", 16, "bold"))
        app_name.pack(pady=(10, 5))

        # バージョン
        version = tk.Label(content_frame, text="Version 1.0.0", font=("Meiryo UI", 10))
        version.pack(pady=5)

        # 区切り線
        separator = tk.Frame(content_frame, height=2, bg="gray")
        separator.pack(fill=tk.X, pady=15)

        # 説明
        description = tk.Label(content_frame, text="PDF/画像ファイルを表示し、マウス座標を\nリアルタイムで確認できるビューアーです",
                              font=("Meiryo UI", 10), justify=tk.CENTER)
        description.pack(pady=10)

        # 作成者
        author = tk.Label(content_frame, text="Created by: 片岡 哲兵", font=("Meiryo UI", 10))
        author.pack(pady=5)

        # ライセンス
        license_label = tk.Label(content_frame, text="License: MIT License", font=("Meiryo UI", 9))
        license_label.pack(pady=5)

        # since
        since_label = tk.Label(content_frame, text="Last Issue Date: 2025-11-13", font=("Meiryo UI", 9))
        since_label.pack(pady=2)

        # 問い合わせURL
        contact_label = tk.Label(content_frame, text="お問い合わせ:", font=("Meiryo UI", 9))
        contact_label.pack(pady=(15, 5))

        contact_url = "https://teppy.link/bbs"  # ここに実際のURLを設定
        url_label = tk.Label(content_frame, text=contact_url, font=("Meiryo UI", 9, "underline"),
                            fg="blue", cursor="hand2")
        url_label.pack(pady=2)
        url_label.bind("<Button-1>", lambda e: webbrowser.open(contact_url))

        message_label = tk.Label(content_frame, text="開発の雑談でメッセージを送ってください", font=("Meiryo UI", 9))
        message_label.pack(pady=(15, 5))

        # マウスホバー時の効果
        url_label.bind("<Enter>", lambda e: url_label.config(fg="dark blue"))
        url_label.bind("<Leave>", lambda e: url_label.config(fg="blue"))

        # 閉じるボタン
        close_btn = tk.Button(about_window, text="閉じる", command=about_window.destroy, width=10, font=("Meiryo UI", 9))
        close_btn.pack(pady=8)


def main():
    root = TkinterDnD.Tk()  # ドラッグアンドドロップをサポートするために TkinterDnD.Tk() を使用
    app = PDFViewer(root)

    # コマンドライン引数でファイルが指定されていれば開く
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        ext = file_path.lower()
        if ext.endswith('.pdf') or ext.endswith('.png') or ext.endswith('.jpg') or ext.endswith('.jpeg'):
            app.load_file(file_path)

    root.mainloop()


if __name__ == "__main__":
    main()
