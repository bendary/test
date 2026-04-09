# -*- encoding=utf8 -*-
__author__ = "xiaoshaobin"

import multiprocessing as mp
import os
import re

from airtest.core.api import *
from airtest.core.settings import Settings as ST

WINDOW_LIST_ENV = "AIRTEST_WINDOWS"
WINDOW_TITLE_RE_ENV = "AIRTEST_WINDOW_TITLE_RE"
DEFAULT_WINDOW_TITLE_RE = r".*石器时代觉醒.*"


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


def _run_loop() -> None:
    while True:
        if exists(Template(r"tpl1745563602445.png", record_pos=(0.026, 0.048), resolution=(1600, 900))):
            sleep(3)
            continue

        if exists(Template(r"tpl1745563559764.png", record_pos=(0.029, 0.011), resolution=(1600, 900))):
            touch(Template(r"tpl1745563568158.png", record_pos=(-0.316, 0.229), resolution=(1600, 900)))

        if exists(Template(r"tpl1749019450396.png", record_pos=(0.001, 0.099), resolution=(1600, 900))):
            touch(Template(r"tpl1761728343124.png", record_pos=(0.094, 0.105), resolution=(1352, 797)))
        if exists(Template(r"tpl1745393236621.png", record_pos=(0.451, 0.178), resolution=(1600, 900))):
            touch(Template(r"tpl1745393246603.png", record_pos=(0.451, 0.245), resolution=(1600, 900)))

        sleep(1)


def _worker(window_uri: str) -> None:
    auto_setup(__file__, devices=[window_uri])
    ST.CVSTRATEGY = ["tpl", "brisk"]
    print(f"[INFO] 已连接窗口: {window_uri}")
    _run_loop()


def main() -> None:
    uris = _resolve_window_uris()
    if len(uris) == 1:
        _worker(uris[0])
        return

    workers: list[mp.Process] = []
    for uri in uris:
        process = mp.Process(target=_worker, args=(uri,))
        process.start()
        workers.append(process)
        print(f"[INFO] 启动窗口任务: {uri}, pid={process.pid}")

    for process in workers:
        process.join()


if __name__ == "__main__":
    mp.freeze_support()
    main()





        


