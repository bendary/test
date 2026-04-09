from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path


TEMPLATE_PATTERN = re.compile(r"""Template\(\s*r?['"]([^'"]+?\.png)['"]""")
PNG_STRING_PATTERN = re.compile(r"""['"]([^'"]+?\.png)['"]""")


def _read_text(script_path: Path) -> str:
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return script_path.read_text(encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"读取脚本失败: {script_path}") from last_error


def _resolve_path(script_path: Path, raw_path: str) -> Path:
    raw = raw_path.strip().replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate
    return (script_path.parent / candidate).resolve()


def _strip_comments(content: str) -> str:
    reader = io.StringIO(content).readline
    tokens: list[tokenize.TokenInfo] = []
    try:
        for token in tokenize.generate_tokens(reader):
            if token.type == tokenize.COMMENT:
                continue
            tokens.append(token)
    except tokenize.TokenError as exc:
        raise RuntimeError("脚本语法不完整，无法解析截图路径") from exc
    return tokenize.untokenize(tokens)


def _extract_png_refs(content: str) -> list[str]:
    ordered: list[tuple[int, str]] = []
    for match in TEMPLATE_PATTERN.finditer(content):
        ordered.append((match.start(1), match.group(1)))
    for match in PNG_STRING_PATTERN.finditer(content):
        ordered.append((match.start(1), match.group(1)))
    ordered.sort(key=lambda item: item[0])
    return [raw for _, raw in ordered]


def parse_screenshot_paths(script_path: str | Path) -> list[Path]:
    script = Path(script_path).resolve()
    if not script.exists():
        raise FileNotFoundError(f"脚本不存在: {script}")

    content = _strip_comments(_read_text(script))
    found: list[Path] = []
    seen: set[str] = set()

    for raw in _extract_png_refs(content):
        path_obj = _resolve_path(script, raw)
        key = str(path_obj).lower()
        if key not in seen:
            seen.add(key)
            found.append(path_obj)
    return found
