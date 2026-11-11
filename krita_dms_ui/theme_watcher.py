"""KDE 颜色方案热重载。

Krita 的 ``ThemeManager`` 只在启动或手动切换主题时读 ``.colors``；
matugen / DMS 换壁纸后会实时改写颜色方案文件，但 Krita 没有文件监听，
所以必须重启才能生效。

本模块监听 ``kritarc`` 与 ``color-schemes`` 目录，按当前主题名重新解析
``.colors`` 并套到 ``QApplication`` 上。后续的 QSS / 语义色刷新仍然交给
``__init__.py`` 里已有的 ``paletteChanged`` 链路，本模块不碰样式。
"""

from pathlib import Path

from .qt_compat import (
    COLOR_GROUP,
    COLOR_ROLE,
    QColor,
    QFileSystemWatcher,
    QObject,
    QPalette,
    QStandardPaths,
    QTimer,
    STANDARD_PATH,
)

_DEBOUNCE_MS = 300
_FALLBACK_WINDOW = QColor("#1e1f24")
_FALLBACK_TEXT = QColor("#e3e1e9")

# 用于判断颜色是否真的变化（避免 matugen 重写同色文件时重复 setPalette）
_SIGNATURE_ROLES = (
    COLOR_ROLE.Window,
    COLOR_ROLE.WindowText,
    COLOR_ROLE.Base,
    COLOR_ROLE.Text,
    COLOR_ROLE.Button,
    COLOR_ROLE.ButtonText,
    COLOR_ROLE.Highlight,
    COLOR_ROLE.HighlightedText,
    COLOR_ROLE.ToolTipBase,
    COLOR_ROLE.ToolTipText,
)


# ---------------------------------------------------------------------------
# .colors 解析
# ---------------------------------------------------------------------------

def _config_path():
    base = QStandardPaths.writableLocation(STANDARD_PATH.GenericConfigLocation)
    return Path(base or (Path.home() / ".config")) / "kritarc"


def _scheme_dirs():
    """Krita 搜索颜色方案的目录（用户目录优先）。"""
    dirs = []
    for base in QStandardPaths.standardLocations(STANDARD_PATH.GenericDataLocation):
        dirs.append(Path(base) / "color-schemes")
    dirs.append(Path.home() / ".local/share/krita/color-schemes")
    dirs.append(Path("/usr/share/krita/color-schemes"))

    seen = set()
    result = []
    for directory in dirs:
        if directory in seen or not directory.is_dir():
            continue
        seen.add(directory)
        result.append(directory)
    return result


def _parse_ini(path):
    """极简 KConfig INI 解析：只处理 ``[Section]`` 与 ``key=value``。"""
    sections = {}
    current = None
    try:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return sections

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if current is None or "=" not in line:
            continue
        key, value = line.split("=", 1)
        sections[current][key.strip()] = value.strip()
    return sections


def _parse_color(raw):
    """解析 ``R,G,B`` / ``R,G,B,A``，顺便兼容 ``#RRGGBB``。"""
    if not raw:
        return None
    text = raw.strip().strip('"')
    parts = [part.strip() for part in text.split(",")]
    if len(parts) in (3, 4):
        try:
            channels = [int(part) for part in parts]
        except ValueError:
            channels = None
        if channels is not None and all(0 <= value <= 255 for value in channels):
            if len(channels) == 3:
                channels.append(255)
            return QColor(*channels)
    color = QColor(text)
    return color if color.isValid() else None


def _mix(fg, bg, weight):
    weight = max(0.0, min(1.0, weight))
    return QColor(
        round(fg.red() * weight + bg.red() * (1 - weight)),
        round(fg.green() * weight + bg.green() * (1 - weight)),
        round(fg.blue() * weight + bg.blue() * (1 - weight)),
        round(fg.alpha() * weight + bg.alpha() * (1 - weight)),
    )


def _shade(color, amount):
    """近似 KColorScheme 的 shade 角色（正值提亮，负值压暗）。"""
    target = QColor("#ffffff") if amount >= 0 else QColor("#000000")
    return _mix(target, color, abs(amount))


def _pick(section, key, fallback):
    return _parse_color(section.get(key)) or fallback


def read_palette(path, base_palette=None):
    """把 ``.colors`` 转成 QPalette；文件无效时返回 None。

    映射与 Krita 的 ``ThemeManager::slotChangePalette()`` 一致；Light /
    Midlight / Mid / Dark / Shadow 用近似 shade，主要供 Qt 的 3D 边框使用。
    """
    ini = _parse_ini(path)
    window = ini.get("Colors:Window")
    if not window:
        return None

    view = ini.get("Colors:View", window)
    button = ini.get("Colors:Button", window)
    selection = ini.get("Colors:Selection", window)
    tooltip = ini.get("Colors:Tooltip", window)

    window_bg = _pick(window, "BackgroundNormal", _FALLBACK_WINDOW)
    window_fg = _pick(window, "ForegroundNormal", _FALLBACK_TEXT)
    view_bg = _pick(view, "BackgroundNormal", window_bg)
    view_fg = _pick(view, "ForegroundNormal", window_fg)
    button_bg = _pick(button, "BackgroundNormal", window_bg)
    button_fg = _pick(button, "ForegroundNormal", window_fg)
    selection_bg = _pick(selection, "BackgroundNormal", view_fg)
    selection_fg = _pick(selection, "ForegroundNormal", view_bg)
    tooltip_bg = _pick(tooltip, "BackgroundNormal", window_bg)
    tooltip_fg = _pick(tooltip, "ForegroundNormal", window_fg)

    active = {
        COLOR_ROLE.Window: window_bg,
        COLOR_ROLE.WindowText: window_fg,
        COLOR_ROLE.Base: view_bg,
        COLOR_ROLE.Text: view_fg,
        COLOR_ROLE.Button: button_bg,
        COLOR_ROLE.ButtonText: button_fg,
        COLOR_ROLE.Highlight: selection_bg,
        COLOR_ROLE.HighlightedText: selection_fg,
        COLOR_ROLE.ToolTipBase: tooltip_bg,
        COLOR_ROLE.ToolTipText: tooltip_fg,
        COLOR_ROLE.PlaceholderText: _pick(view, "ForegroundInactive", view_fg),
        COLOR_ROLE.AlternateBase: _pick(view, "BackgroundAlternate", view_bg),
        COLOR_ROLE.Link: _pick(view, "ForegroundLink", selection_bg),
        COLOR_ROLE.LinkVisited: _pick(view, "ForegroundVisited", view_fg),
        COLOR_ROLE.Light: _shade(window_bg, 0.10),
        COLOR_ROLE.Midlight: _shade(window_bg, 0.05),
        COLOR_ROLE.Mid: _shade(window_bg, -0.06),
        COLOR_ROLE.Dark: _shade(window_bg, -0.14),
        COLOR_ROLE.Shadow: _shade(window_bg, -0.22),
    }

    palette = QPalette(base_palette) if base_palette is not None else QPalette()
    for group in (COLOR_GROUP.Active, COLOR_GROUP.Inactive):
        for role, color in active.items():
            palette.setColor(group, role, color)

    # Disabled 组：背景不变，前景压暗（近似 KColorScheme 的 disabled effect）
    disabled = dict(active)
    for role in (
        COLOR_ROLE.WindowText,
        COLOR_ROLE.Text,
        COLOR_ROLE.ButtonText,
        COLOR_ROLE.HighlightedText,
        COLOR_ROLE.ToolTipText,
    ):
        background = {
            COLOR_ROLE.WindowText: window_bg,
            COLOR_ROLE.Text: view_bg,
            COLOR_ROLE.ButtonText: button_bg,
            COLOR_ROLE.HighlightedText: selection_bg,
            COLOR_ROLE.ToolTipText: tooltip_bg,
        }[role]
        disabled[role] = _mix(active[role], background, 0.45)
    for role, color in disabled.items():
        palette.setColor(COLOR_GROUP.Disabled, role, color)

    accent = getattr(COLOR_ROLE, "Accent", None)
    if accent is not None:
        palette.setColor(COLOR_ROLE.Accent, selection_bg)

    return palette


def _read_theme_name(path):
    ini = _parse_ini(path)
    for section in ("theme", "Theme", "General"):
        name = ini.get(section, {}).get("Theme")
        if name:
            return name.strip()
    return None


def _scheme_map(dirs):
    """名称 → 文件；用户目录优先，同名保留第一个。"""
    result = {}
    for directory in dirs:
        for path in sorted(directory.glob("*.colors")):
            ini = _parse_ini(path)
            name = ini.get("General", {}).get("Name") or path.stem
            result.setdefault(name.strip(), path)
    return result


def _signature(path, palette):
    colors = tuple(palette.color(COLOR_GROUP.Active, role).rgba() for role in _SIGNATURE_ROLES)
    return (str(path),) + colors


# 只比较这些角色来判断「Krita 有没有读过这个文件」：
# Highlight / HighlightedText 会被插件改写成 primary-container，
# shade / link 角色我们又只能近似，排除它们避免误判。
_CORE_ROLES = (
    COLOR_ROLE.Window,
    COLOR_ROLE.WindowText,
    COLOR_ROLE.Base,
    COLOR_ROLE.Text,
    COLOR_ROLE.Button,
    COLOR_ROLE.ButtonText,
    COLOR_ROLE.ToolTipBase,
    COLOR_ROLE.ToolTipText,
)


def _core_colors(palette):
    return tuple(palette.color(COLOR_GROUP.Active, role).rgba() for role in _CORE_ROLES)


# ---------------------------------------------------------------------------
# 监听
# ---------------------------------------------------------------------------

class ThemeWatcher(QObject):
    """监听 kritarc / color-schemes，把当前主题重新套到 QApplication。"""

    def __init__(self, app, parent=None):
        super().__init__(parent if parent is not None else app)
        self.app = app
        self._watcher = QFileSystemWatcher(self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_DEBOUNCE_MS)
        self._timer.timeout.connect(self.reload)
        self._watcher.fileChanged.connect(self._schedule)
        self._watcher.directoryChanged.connect(self._schedule)
        self._watched = set()
        self._last_signature = None

        self._watch_config()
        for directory in _scheme_dirs():
            self._watch_path(directory)

        resolved = self._resolve()
        if resolved is not None:
            path, palette, signature = resolved
            self._watch_path(path)
            self._last_signature = signature
            # Krita 启动时若没读过这个文件（例如文件比进程新），这里补一次
            if _core_colors(palette) != _core_colors(self.app.palette()):
                self._apply(path, palette)

    # ---- 监听 ----------------------------------------------------------

    def _watch_path(self, path):
        text = str(path)
        if text in self._watched or not Path(text).exists():
            return
        if self._watcher.addPath(text):
            self._watched.add(text)

    def _watch_config(self):
        # 只监听 kritarc 文件本身；主题切换时 Krita 会自己应用新调色板，
        # 这里主要是在壁纸变化后重新确认当前主题名。
        self._watch_path(_config_path())

    def _schedule(self, _path=None):
        if not self._timer.isActive():
            self._timer.start()

    # ---- 解析 / 应用 ---------------------------------------------------

    def _resolve(self):
        theme = _read_theme_name(_config_path())
        if not theme or theme == "System":
            return None

        path = _scheme_map(_scheme_dirs()).get(theme)
        if path is None:
            return None

        palette = read_palette(path, self.app.palette())
        if palette is None:
            return None
        return path, palette, _signature(path, palette)

    def _current_signature(self):
        resolved = self._resolve()
        return resolved[2] if resolved is not None else None

    def reload(self):
        """防抖结束后调用：颜色没变就不动。"""
        resolved = self._resolve()
        if resolved is None:
            return

        path, palette, signature = resolved
        if signature == self._last_signature:
            self._watch_path(path)
            return

        self._last_signature = signature
        self._watch_path(path)
        self._apply(path, palette)

    def _apply(self, path, palette):
        self.app.setProperty("KDE_COLOR_SCHEME_PATH", str(path))
        self.app.setPalette(palette)
