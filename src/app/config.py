import sys
from pathlib import Path


def _resolve_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _resolve_project_root()

def _pick_first_existing(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


DEFAULT_SCRIPTS = {
    "nisi": _pick_first_existing(
        PROJECT_ROOT / "scripts" / "nisi55.air" / "nisi55.py",
        PROJECT_ROOT / "scripts" / "nisi.air" / "nisi.py",
        PROJECT_ROOT / "scripts" / "nisi.py",
    ),
    "jjc": _pick_first_existing(
        PROJECT_ROOT / "scripts" / "jjc.air" / "jjc.py",
        PROJECT_ROOT / "scripts" / "jjc.py",
    ),
}
