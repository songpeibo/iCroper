# -*- coding: utf-8 -*-
"""项目内 SVG 图标路径（resources/icons），兼容开发与打包运行。"""
from __future__ import annotations

import sys
from pathlib import Path


def _icon_dir_candidates() -> list[Path]:
    project_root = Path(__file__).resolve().parent.parent
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else None
    meipass = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else None

    dirs: list[Path] = [project_root / "resources" / "icons"]
    if exe_dir is not None:
        dirs.append(exe_dir / "resources" / "icons")
    if meipass is not None and str(meipass):
        dirs.append(meipass / "resources" / "icons")
    dirs.append(Path.cwd() / "resources" / "icons")
    return dirs


def icon_path(filename: str) -> str:
    """返回可访问图标绝对路径；找不到返回空字符串。"""
    for d in _icon_dir_candidates():
        p = d / filename
        if p.exists() and p.is_file():
            return str(p)
    return ""
