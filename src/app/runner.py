from __future__ import annotations

import contextlib
import io
import runpy
import subprocess
import sys
import threading
import traceback
from pathlib import Path
from typing import Callable

from .config import PROJECT_ROOT


LogCallback = Callable[[str], None]
DoneCallback = Callable[[int], None]


class _CallbackWriter(io.TextIOBase):
    def __init__(self, on_log: LogCallback) -> None:
        self._on_log = on_log

    def write(self, s: str) -> int:
        if s:
            self._on_log(s)
        return len(s)

    def flush(self) -> None:
        return None


def _run_script_in_process(script: Path, on_log: LogCallback) -> int:
    out = _CallbackWriter(on_log)
    err = _CallbackWriter(on_log)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            runpy.run_path(str(script), run_name="__main__")
            return 0
        except SystemExit as exc:
            code = exc.code
            if isinstance(code, int):
                return code
            if code is None:
                return 0
            on_log(f"{code}\n")
            return 1
        except Exception:  # noqa: BLE001
            on_log(traceback.format_exc())
            return 1


def run_script(script_path: str | Path, on_log: LogCallback, on_done: DoneCallback | None = None) -> None:
    script = Path(script_path).resolve()
    if not script.exists():
        raise FileNotFoundError(f"脚本不存在: {script}")

    def _worker() -> None:
        if getattr(sys, "frozen", False):
            on_log(f"$ in-process {script}\n")
            return_code = _run_script_in_process(script, on_log)
        else:
            cmd = [sys.executable, str(script)]
            on_log(f"$ {' '.join(cmd)}\n")
            try:
                process = subprocess.Popen(  # noqa: S603
                    cmd,
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
            except Exception as exc:  # noqa: BLE001
                on_log(f"[ERROR] 启动失败: {exc}\n")
                if on_done:
                    on_done(-1)
                return

            assert process.stdout is not None
            for line in process.stdout:
                on_log(line)

            return_code = process.wait()

        on_log(f"\n[INFO] 进程退出码: {return_code}\n")
        if on_done:
            on_done(return_code)

    threading.Thread(target=_worker, daemon=True).start()
