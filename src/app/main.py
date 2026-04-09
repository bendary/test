from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from app.ui import AppUI
else:
    from .ui import AppUI


def main() -> None:
    try:
        root = tk.Tk()
        AppUI(root)
        root.mainloop()
    except Exception as exc:  # noqa: BLE001
        messagebox.showerror("程序异常", str(exc))
        raise


if __name__ == "__main__":
    main()
