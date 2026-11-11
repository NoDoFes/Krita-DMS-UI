"""SVG 图标素材库。

``assets/icons/`` 里放带 ``{{COLOR}}`` 占位的模板；主题变化时按当前语义
token 渲染成真实文件，再由 QSS 用 ``image: url(...)`` 引用。

这样既不用为浅色 / 深色各准备一套图片，也不需要 PNG：图标颜色永远等于
``styles.get_theme_colors()`` 里的文字色 / 禁用色。渲染结果按颜色命名缓存在
用户缓存目录，颜色没变时不会重复写盘。
"""

from pathlib import Path

from .qt_compat import QStandardPaths, STANDARD_PATH

_TEMPLATE_DIR = Path(__file__).with_name("assets") / "icons"
_cache_root = QStandardPaths.writableLocation(STANDARD_PATH.CacheLocation)
_CACHE_DIR = (
    Path(_cache_root) if _cache_root else Path.home() / ".cache"
) / "dms_ui_icons"

# QSS token → (模板文件名, 颜色 token)
_SPECS = {
    "SPIN_UP_ICON": ("arrow_up", "TEXT"),
    "SPIN_DOWN_ICON": ("arrow_down", "TEXT"),
    "SPIN_UP_DISABLED_ICON": ("arrow_up", "TEXT_DISABLED"),
    "SPIN_DOWN_DISABLED_ICON": ("arrow_down", "TEXT_DISABLED"),
}


def _safe_color(value):
    """只接受 ``#RRGGBB``，避免把任意字符串写进 SVG / 文件名。"""
    value = (value or "").strip()
    if len(value) == 7 and value.startswith("#"):
        try:
            int(value[1:], 16)
        except ValueError:
            return None
        return value
    return None


def _write_icon(template_name, color):
    """渲染单个图标，返回路径；失败返回 None（QSS 会退回不显示）。"""
    path = _CACHE_DIR / f"{template_name}-{color[1:].lower()}.svg"
    if path.exists():
        return path

    try:
        template = (_TEMPLATE_DIR / f"{template_name}.svg").read_text(encoding="utf-8")
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(template.replace("{{COLOR}}", color), encoding="utf-8")
    except OSError:
        return None
    return path


def _drop_stale(keep):
    """清掉其它主题留下的文件，缓存目录只保留当前这套图标。"""
    try:
        for item in _CACHE_DIR.iterdir():
            if item.name not in keep and item.suffix == ".svg":
                item.unlink()
    except OSError:
        pass


def prepare_icons(colors):
    """按当前主题渲染图标，返回 ``{QSS token: url(...)}``。

    只在颜色变化时写盘；写入失败时对应 token 退化为 ``none``，
    不影响其余样式加载。
    """
    tokens = {}
    keep = set()

    for token, (template_name, color_token) in _SPECS.items():
        color = _safe_color(colors.get(color_token))
        path = _write_icon(template_name, color) if color else None
        if path is None:
            tokens[token] = "none"
            continue
        keep.add(path.name)
        tokens[token] = 'url("{}")'.format(path.as_posix())

    _drop_stale(keep)
    return tokens


__all__ = ["prepare_icons"]
