# 变更记录

## 2026-04-09 09:04:41 +0800
- 修改内容：初始化 notes 记录文件，建立最小历史追踪结构。
- 涉及文件：`notes/CHANGELOG.md`
- 修改原因：满足“先查阅历史记录，若缺失则创建最小 notes 结构并记录本次操作”要求。
- 执行命令：
  - `ls -la`
  - `ls -la notes`
  - `find . -maxdepth 3 -print | sort`

## 2026-04-09 09:05:00 +0800
- 修改内容：实现 tkinter GUI 程序骨架，支持脚本选择、截图路径解析、截图预览、覆盖截图、脚本执行与日志输出。
- 涉及文件：
  - `src/app/main.py`
  - `src/app/ui.py`
  - `src/app/script_parser.py`
  - `src/app/runner.py`
  - `src/app/config.py`
  - `src/app/__init__.py`
  - `pyproject.toml`
  - `notes/2026-04-09_changes.txt`
- 修改原因：按需求先完成可扩展框架，后续直接替换 `nisi/jjc` 脚本路径即可接入。
- 执行命令：
  - `mkdir -p src/app notes`
  - `python3 -m compileall src/app`

## 2026-04-09 09:07:44 +0800
- 修改内容：在现有项目基础上用 uv 补充依赖，新增 `airtest`（按平台条件）与 `pillow`。
- 涉及文件：`pyproject.toml`、`uv.lock`、`.venv/`
- 修改原因：满足最小环境初始化且不破坏当前 macOS 开发机（`airtest` 依赖 `pywin32`，仅在 Windows 安装）。
- 执行命令：
  - `uv add "airtest>=1.4.3; sys_platform == 'win32'"`
  - `uv add pillow`

## 2026-04-09 09:08:31 +0800
- 修改内容：验证项目入口与依赖版本；确认 `waigua-win = "app.main:main"` 可被 uv 运行环境导入。
- 涉及文件：`notes/CHANGELOG.md`
- 修改原因：确保初始化可运行、并形成可追溯记录；同时避免改动已有 GUI 文件。
- 执行命令：
  - `uv run python -c "import app.main as m; print('main_ok', callable(m.main))"`
  - `uv run python -c "import tomllib, pathlib; ...读取 uv.lock 提取 airtest/pillow 版本..."`
