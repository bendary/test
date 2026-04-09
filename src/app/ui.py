from __future__ import annotations

import base64
import time
import tkinter as tk
from io import BytesIO
from platform import system
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab, ImageOps

from .config import DEFAULT_SCRIPTS
from .runner import run_script
from .script_parser import parse_screenshot_paths
from .window_detector import DetectedWindow, capture_window_preview, detect_windows


class AppUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("脚本与截图管理器")
        self.root.geometry("1200x700")

        self.scripts = {k: Path(v).resolve() for k, v in DEFAULT_SCRIPTS.items()}
        self.current_script_key: str | None = None
        self.current_image_path: Path | None = None
        self.image_items: dict[str, Path] = {}
        self.image_thumb_refs: list[tk.PhotoImage] = []
        self.detected_windows: list[DetectedWindow] = []
        self.window_preview_ref: tk.PhotoImage | None = None
        self.window_uri_var = tk.StringVar(value="")
        self.script_path_var = tk.StringVar(value="")
        self.thumb_size = (260, 140)

        self._build_layout()
        self._load_script_names()
        self._detect_stone_windows(silent=True)

    def _photo_from_pil(self, image: Image.Image) -> tk.PhotoImage:
        with BytesIO() as buffer:
            image.save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return tk.PhotoImage(data=encoded, master=self.root)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main.grid(row=0, column=0, sticky="nsew")

        left = ttk.Frame(main, padding=8)
        center = ttk.Frame(main, padding=8)
        right = ttk.Frame(main, padding=8)

        main.add(left, weight=1)
        main.add(center, weight=2)
        main.add(right, weight=2)

        script_frame = ttk.LabelFrame(left, text="脚本选择")
        script_frame.pack(fill="both", expand=True)
        script_frame.rowconfigure(1, weight=1)
        script_frame.columnconfigure(0, weight=1)

        ttk.Label(script_frame, text="脚本").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 2))
        self.script_list = tk.Listbox(script_frame, exportselection=False, height=8)
        self.script_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 4))
        self.script_list.bind("<<ListboxSelect>>", self._on_script_select)

        script_btn_row = ttk.Frame(script_frame)
        script_btn_row.grid(row=2, column=0, sticky="ew", padx=6, pady=(2, 0))
        script_btn_row.columnconfigure((0, 1), weight=1)
        ttk.Button(script_btn_row, text="设置脚本路径", command=self._set_script_path).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(script_btn_row, text="执行脚本", command=self._run_current_script).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )
        ttk.Label(script_frame, textvariable=self.script_path_var, justify="left", wraplength=240).grid(
            row=3, column=0, sticky="w", padx=6, pady=(8, 6)
        )

        ttk.Label(center, text="识别到的截图列表").pack(anchor="w")
        image_btn_row = ttk.Frame(center)
        image_btn_row.pack(fill="x", pady=(4, 4))
        ttk.Button(image_btn_row, text="截图并覆盖（当前选中）", command=self._capture_and_overwrite).pack(
            side="left"
        )
        ttk.Button(image_btn_row, text="刷新截图列表", command=self._refresh_images).pack(
            side="left", padx=(8, 0)
        )

        style = ttk.Style(self.root)
        style.configure("ImageList.Treeview", rowheight=self.thumb_size[1] + 8)

        tree_frame = ttk.Frame(center)
        tree_frame.pack(fill="both", expand=True, pady=(4, 0))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.image_list = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
            style="ImageList.Treeview",
        )
        self.image_list.column("#0", width=self.thumb_size[0] + 8, anchor="center", stretch=True)
        self.image_list.grid(row=0, column=0, sticky="nsew")
        self.image_list.bind("<<TreeviewSelect>>", self._on_image_select)

        image_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.image_list.yview)
        image_scroll.grid(row=0, column=1, sticky="ns")
        self.image_list.configure(yscrollcommand=image_scroll.set)

        stone_frame = ttk.LabelFrame(right, text="石器窗口预览")
        stone_frame.pack(fill="both", expand=True)
        stone_frame.rowconfigure(1, weight=3)
        stone_frame.rowconfigure(2, weight=2)
        stone_frame.columnconfigure(0, weight=1)

        stone_button_row = ttk.Frame(stone_frame)
        stone_button_row.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 2))
        ttk.Button(stone_button_row, text="自动检测窗口", command=self._detect_stone_windows).pack(
            side="left"
        )
        ttk.Button(stone_button_row, text="刷新预览", command=self._refresh_window_preview).pack(
            side="left", padx=(8, 0)
        )

        self.window_preview_label = ttk.Label(stone_frame, text="请先检测并选择石器窗口")
        self.window_preview_label.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)

        self.window_list = tk.Listbox(stone_frame, exportselection=False, height=7)
        self.window_list.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 4))
        self.window_list.bind("<<ListboxSelect>>", self._on_window_select)

        ttk.Label(stone_frame, textvariable=self.window_uri_var, justify="left", wraplength=360).grid(
            row=3, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        if system() != "Windows":
            self.window_uri_var.set("当前系统非 Windows，窗口检测仅在 Windows 可用。")

        log_frame = ttk.LabelFrame(right, text="日志")
        log_frame.pack(fill="both", expand=False, pady=(8, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=8, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

    def _load_script_names(self) -> None:
        self.script_list.delete(0, tk.END)
        for key in self.scripts:
            self.script_list.insert(tk.END, key)
        if self.script_list.size() > 0:
            self.script_list.selection_set(0)
            self._on_script_select()

    def _get_selected_script_key(self) -> str | None:
        selection = self.script_list.curselection()
        if not selection:
            return None
        return self.script_list.get(selection[0])

    def _on_script_select(self, _event: object | None = None) -> None:
        key = self._get_selected_script_key()
        if not key:
            return
        self.current_script_key = key
        self.script_path_var.set(str(self.scripts[key]))
        self._refresh_images()

    def _set_script_path(self) -> None:
        if not self.current_script_key:
            messagebox.showwarning("未选择脚本", "请先选择 nisi 或 jjc。")
            return

        initial = self.scripts[self.current_script_key]
        initial_dir = str(initial.parent if initial.parent.exists() else Path.cwd())
        selected = filedialog.askopenfilename(
            title=f"选择 {self.current_script_key} 脚本",
            initialdir=initial_dir,
            filetypes=[("Python 脚本", "*.py"), ("All files", "*.*")],
        )
        if not selected:
            return

        resolved = Path(selected).resolve()
        self.scripts[self.current_script_key] = resolved
        self.script_path_var.set(str(resolved))
        self._log(f"[INFO] 已更新脚本路径: {self.current_script_key} -> {resolved}\n")
        self._refresh_images()

    def _refresh_images(self, keep_path: Path | None = None) -> None:
        self.image_list.delete(*self.image_list.get_children())
        self.image_items.clear()
        self.image_thumb_refs.clear()
        selected_target = keep_path if keep_path is not None else self.current_image_path
        self.current_image_path = None

        if not self.current_script_key:
            return
        script_path = self.scripts[self.current_script_key]

        try:
            paths = parse_screenshot_paths(script_path)
        except Exception as exc:  # noqa: BLE001
            self._log(f"[ERROR] 解析截图路径失败: {exc}\n")
            if script_path.exists():
                messagebox.showerror("解析失败", str(exc))
            return

        selected_item_id: str | None = None
        for path in paths:
            thumb = self._build_list_thumbnail(path)
            item_id = self.image_list.insert(
                "",
                "end",
                text="",
                image=thumb if thumb is not None else "",
            )
            self.image_items[item_id] = path
            if thumb is not None:
                self.image_thumb_refs.append(thumb)
            if selected_target is not None and path == selected_target:
                selected_item_id = item_id

        if selected_item_id is None and paths:
            selected_item_id = self.image_list.get_children()[0]

        if selected_item_id is not None:
            self.image_list.selection_set(selected_item_id)
            self.image_list.focus(selected_item_id)
            self.current_image_path = self.image_items[selected_item_id]

        self._log(f"[INFO] {self.current_script_key}: 识别到 {len(paths)} 个截图路径\n")

    def _on_image_select(self, _event: object | None = None) -> None:
        selection = self.image_list.selection()
        if not selection:
            return
        item_id = selection[0]
        image_path = self.image_items.get(item_id)
        if image_path is None:
            return
        self.current_image_path = image_path

    def _build_placeholder_thumbnail(self) -> tk.PhotoImage:
        canvas_width, canvas_height = self.thumb_size
        canvas = Image.new("RGBA", (canvas_width, canvas_height), (45, 45, 45, 255))
        return self._photo_from_pil(canvas)

    def _build_list_thumbnail(self, image_path: Path) -> tk.PhotoImage:
        if not image_path.exists():
            return self._build_placeholder_thumbnail()
        try:
            canvas_width, canvas_height = self.thumb_size
            with Image.open(image_path) as raw:
                thumb = raw.convert("RGBA")
            thumb = ImageOps.contain(thumb, (canvas_width - 8, canvas_height - 8))
            canvas = Image.new("RGBA", (canvas_width, canvas_height), (30, 30, 30, 255))
            left = (canvas_width - thumb.width) // 2
            top = (canvas_height - thumb.height) // 2
            canvas.paste(thumb, (left, top), thumb)
            return self._photo_from_pil(canvas)
        except Exception:
            return self._build_placeholder_thumbnail()

    def _set_window_preview_text(self, text: str) -> None:
        self.window_preview_ref = None
        self.window_preview_label.configure(image="", text=text)

    def _detect_stone_windows(self, silent: bool = False) -> None:
        self.window_list.delete(0, tk.END)
        self.detected_windows = []
        self.window_uri_var.set("")
        self._set_window_preview_text("请先检测并选择石器窗口")

        if system() != "Windows":
            if not silent:
                messagebox.showinfo("提示", "窗口自动检测仅支持 Windows。")
            self.window_uri_var.set("当前系统非 Windows，窗口检测仅在 Windows 可用。")
            return

        try:
            windows = detect_windows("石器时代觉醒")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[ERROR] 检测石器窗口失败: {exc}\n")
            if not silent:
                messagebox.showerror("检测失败", str(exc))
            return

        self.detected_windows = windows
        if not windows:
            self.window_uri_var.set("未检测到石器时代觉醒窗口")
            self._set_window_preview_text("未检测到石器时代觉醒窗口")
            self._log("[INFO] 未检测到石器时代觉醒窗口\n")
            return

        for idx, window in enumerate(windows, start=1):
            self.window_list.insert(tk.END, f"{idx}. {window.title} (HWND:{window.handle})")

        self.window_list.selection_set(0)
        self.window_list.activate(0)
        self._on_window_select()
        self._log(f"[INFO] 检测到 {len(windows)} 个石器时代觉醒窗口\n")

    def _on_window_select(self, _event: object | None = None) -> None:
        selection = self.window_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index < 0 or index >= len(self.detected_windows):
            return

        window = self.detected_windows[index]
        self.window_uri_var.set(f"{window.title}\n{window.airtest_uri}")
        self._refresh_window_preview()

    def _refresh_window_preview(self) -> None:
        selection = self.window_list.curselection()
        if not selection:
            self._set_window_preview_text("请先检测并选择石器窗口")
            return
        index = selection[0]
        if index < 0 or index >= len(self.detected_windows):
            self._set_window_preview_text("请先检测并选择石器窗口")
            return

        window = self.detected_windows[index]
        try:
            screenshot = capture_window_preview(window)
            photo = self._photo_from_pil(screenshot)
        except Exception as exc:  # noqa: BLE001
            msg = f"窗口预览失败: {exc}"
            self._set_window_preview_text(msg)
            self._log(f"[ERROR] {msg}\n")
            return

        self.window_preview_ref = photo
        self.window_preview_label.configure(image=photo, text="")

    def _capture_and_overwrite(self) -> None:
        if not self.current_image_path:
            messagebox.showwarning("未选择截图", "请先从中间列表选择一个截图路径。")
            return

        region: tuple[int, int, int, int] | None = None
        try:
            self.root.withdraw()
            self.root.update_idletasks()
            time.sleep(0.25)
            screenshot = ImageGrab.grab()
            region = self._select_capture_region(screenshot)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("截图失败", str(exc))
            self._log(f"[ERROR] 截图失败: {exc}\n")
            return
        finally:
            self.root.deiconify()
            self.root.lift()

        if not region:
            self._log("[INFO] 已取消重新截图\n")
            return

        left, top, right, bottom = region
        if right <= left or bottom <= top:
            messagebox.showwarning("区域无效", "请拖拽一个有效的截图区域。")
            return

        cropped = screenshot.crop((left, top, right, bottom))
        try:
            self.current_image_path.parent.mkdir(parents=True, exist_ok=True)
            cropped.save(self.current_image_path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("保存失败", str(exc))
            self._log(f"[ERROR] 保存截图失败: {exc}\n")
            return

        self._log(f"[INFO] 已覆盖截图: {self.current_image_path}\n")
        self._refresh_images(keep_path=self.current_image_path)
        messagebox.showinfo("完成", "截图已覆盖。")

    def _select_capture_region(self, screenshot: Image.Image) -> tuple[int, int, int, int] | None:
        width, height = screenshot.size
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-topmost", True)
        overlay.overrideredirect(True)

        canvas = tk.Canvas(overlay, highlightthickness=0, cursor="cross")
        canvas.pack(fill="both", expand=True)

        photo = self._photo_from_pil(screenshot)
        canvas.create_image(0, 0, image=photo, anchor="nw")

        rect = canvas.create_rectangle(0, 0, 0, 0, outline="red", width=2)
        start: tuple[int, int] | None = None
        result: tuple[int, int, int, int] | None = None

        def _clamp(x: int, y: int) -> tuple[int, int]:
            clamped_x = min(max(x, 0), width - 1)
            clamped_y = min(max(y, 0), height - 1)
            return clamped_x, clamped_y

        def _on_press(event: tk.Event[tk.Misc]) -> None:
            nonlocal start
            x, y = _clamp(event.x, event.y)
            start = (x, y)
            canvas.coords(rect, x, y, x, y)

        def _on_drag(event: tk.Event[tk.Misc]) -> None:
            if not start:
                return
            x0, y0 = start
            x1, y1 = _clamp(event.x, event.y)
            canvas.coords(rect, x0, y0, x1, y1)

        def _on_release(event: tk.Event[tk.Misc]) -> None:
            nonlocal result
            if not start:
                return
            x0, y0 = start
            x1, y1 = _clamp(event.x, event.y)
            left = min(x0, x1)
            top = min(y0, y1)
            right = max(x0, x1)
            bottom = max(y0, y1)
            result = (left, top, right, bottom)
            overlay.destroy()

        def _cancel(_event: tk.Event[tk.Misc] | None = None) -> None:
            nonlocal result
            result = None
            overlay.destroy()

        canvas.bind("<ButtonPress-1>", _on_press)
        canvas.bind("<B1-Motion>", _on_drag)
        canvas.bind("<ButtonRelease-1>", _on_release)
        overlay.bind("<Escape>", _cancel)
        overlay.bind("<Button-3>", _cancel)
        overlay.grab_set()
        overlay.focus_force()
        self.root.wait_window(overlay)
        return result

    def _run_current_script(self) -> None:
        if not self.current_script_key:
            messagebox.showwarning("未选择脚本", "请先选择脚本。")
            return

        script_path = self.scripts[self.current_script_key]
        if not script_path.exists():
            messagebox.showerror("脚本不存在", str(script_path))
            return

        self._log(f"[INFO] 开始执行脚本: {script_path}\n")
        try:
            run_script(script_path, self._log)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("执行失败", str(exc))
            self._log(f"[ERROR] 执行失败: {exc}\n")

    def _log(self, text: str) -> None:
        def _append() -> None:
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)

        self.root.after(0, _append)
