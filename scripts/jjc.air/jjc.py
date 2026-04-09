# -*- encoding=utf8 -*-
__author__ = "xiaoshaobin"

import ctypes
import os
import re

from airtest.core.api import *
from airtest.core.settings import Settings as ST

WINDOW_LIST_ENV = "AIRTEST_WINDOWS"
WINDOW_TITLE_RE_ENV = "AIRTEST_WINDOW_TITLE_RE"
DEFAULT_WINDOW_TITLE_RE = r".*石器时代.*"


def _resolve_window_uris() -> list[str]:
    window_list = os.getenv(WINDOW_LIST_ENV, "").strip()
    if window_list:
        uris: list[str] = []
        for raw_uri in window_list.split(","):
            item = raw_uri.strip()
            if not item:
                continue
            if item.startswith("Windows:///"):
                uris.append(item)
            elif item.isdigit():
                uris.append(f"Windows:///{item}")
            else:
                raise ValueError(f"无效窗口配置: {item}，请使用句柄或 Windows:///句柄")
        if not uris:
            raise ValueError(f"{WINDOW_LIST_ENV} 为空，请至少提供一个窗口句柄")
        return uris

    try:
        from pywinauto import Desktop
    except ImportError:
        return ["Windows:///"]

    windows = None
    for backend in ("uia", "win32"):
        try:
            windows = Desktop(backend=backend).windows()
            break
        except Exception:
            continue
    if windows is None:
        return ["Windows:///"]

    title_re = os.getenv(WINDOW_TITLE_RE_ENV, DEFAULT_WINDOW_TITLE_RE)
    matcher = re.compile(title_re)
    uris: list[str] = []
    for win in windows:
        title = (win.window_text() or "").strip()
        if not title or not matcher.search(title):
            continue
        uris.append(f"Windows:///{int(win.handle)}")
    return list(dict.fromkeys(uris)) or ["Windows:///"]


def _extract_handle(window_uri: str) -> int | None:
    if not window_uri.startswith("Windows:///"):
        return None
    raw = window_uri[len("Windows:///") :].split("?", 1)[0].strip()
    if not raw or not raw.isdigit():
        return None
    return int(raw)


def _activate_window(window_handle: int | None) -> None:
    if window_handle is None or os.name != "nt":
        return
    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    user32.ShowWindow(window_handle, SW_RESTORE)
    user32.SetForegroundWindow(window_handle)
    sleep(0.2)


def _run_once() -> None:
    if exists(Template(r"tpl1745393180068.png", record_pos=(-0.394, -0.261), resolution=(1600, 900))):
        touch(Template(r"tpl1745393190018.png", record_pos=(0.001, 0.129), resolution=(1600, 900)))

    if exists(Template(r"tpl1745393205592.png", record_pos=(0.026, 0.05), resolution=(1600, 900))):
        sleep(10)
        return

    if exists(Template(r"tpl1745393236621.png", record_pos=(0.451, 0.178), resolution=(1600, 900))):
        touch(Template(r"tpl1745393246603.png", record_pos=(0.451, 0.245), resolution=(1600, 900)))
    if exists(Template(r"tpl1747125309729.png", record_pos=(-0.004, 0.172), resolution=(1600, 900))):
        touch((909, 730))

    sleep(3)


def main() -> None:
    uris = _resolve_window_uris()
    auto_setup(__file__, devices=[uris[0]])
    ST.CVSTRATEGY = ["tpl", "brisk"]

    targets: list[tuple[str, int | None, str]] = []
    for idx, uri in enumerate(uris):
        dev = device() if idx == 0 else connect_device(uri)
        handle = _extract_handle(uri)
        targets.append((dev.uuid, handle, uri))
        print(f"[INFO] 已连接窗口: {uri}")

    while True:
        for uuid, handle, uri in targets:
            set_current(uuid)
            _activate_window(handle)
            print(f"[INFO] 当前窗口: {uri}")
            _run_once()


if __name__ == "__main__":
    main()








