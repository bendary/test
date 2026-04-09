from __future__ import annotations

from dataclasses import dataclass
from platform import system

from PIL import Image, ImageGrab


@dataclass(frozen=True)
class DetectedWindow:
    title: str
    handle: int
    left: int
    top: int
    right: int
    bottom: int

    @property
    def airtest_uri(self) -> str:
        return f"Windows:///{self.handle}"


def detect_windows(title_keyword: str = "石器时代觉醒") -> list[DetectedWindow]:
    if system() != "Windows":
        return []

    try:
        from pywinauto import Desktop
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("缺少 pywinauto，无法检测 Windows 窗口。") from exc

    windows = None
    last_error: Exception | None = None
    for backend in ("uia", "win32"):
        try:
            windows = Desktop(backend=backend).windows()
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if windows is None:
        raise RuntimeError(f"无法枚举 Windows 窗口: {last_error}") from last_error

    results: list[DetectedWindow] = []
    for win in windows:
        title = (win.window_text() or "").strip()
        if not title or title_keyword not in title:
            continue

        rect = win.rectangle()
        width = int(rect.right) - int(rect.left)
        height = int(rect.bottom) - int(rect.top)
        if width <= 0 or height <= 0:
            continue

        results.append(
            DetectedWindow(
                title=title,
                handle=int(win.handle),
                left=int(rect.left),
                top=int(rect.top),
                right=int(rect.right),
                bottom=int(rect.bottom),
            )
        )
    return results


def capture_window_preview(window: DetectedWindow, max_size: tuple[int, int] = (480, 280)) -> Image.Image:
    if system() != "Windows":
        raise RuntimeError("当前系统不是 Windows，无法预览窗口。")

    screenshot = ImageGrab.grab(
        bbox=(window.left, window.top, window.right, window.bottom),
        all_screens=True,
    ).convert("RGBA")
    screenshot.thumbnail(max_size)
    return screenshot
