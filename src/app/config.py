import sys
from pathlib import Path


def _runtime_roots() -> list[Path]:
    if not getattr(sys, "frozen", False):
        return [Path(__file__).resolve().parents[2]]

    exe_dir = Path(sys.executable).resolve().parent
    roots: list[Path] = [exe_dir]

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass).resolve())

    roots.append((exe_dir / "_internal").resolve())

    deduped: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        deduped.append(root)
    return deduped


def _resolve_project_root() -> Path:
    roots = _runtime_roots()
    for root in roots:
        if (root / "scripts").exists():
            return root
    return roots[0]


PROJECT_ROOT = _resolve_project_root()
ROOT_CANDIDATES = _runtime_roots()


def _pick_first_existing(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _pick_script(*relative_paths: str) -> Path:
    candidates: list[Path] = []
    for root in ROOT_CANDIDATES:
        for rel in relative_paths:
            candidates.append(root / rel)
    return _pick_first_existing(*candidates)


DEFAULT_SCRIPTS = {
    "nisi": _pick_script(
        "scripts/nisi55.air/nisi55.py",
        "scripts/nisi.air/nisi.py",
        "scripts/nisi.py",
    ),
    "jjc": _pick_script(
        "scripts/jjc.air/jjc.py",
        "scripts/jjc.py",
    ),
}
