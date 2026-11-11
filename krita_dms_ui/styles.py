"""主题层：QPalette → 语义色 → 全局 QSS。

颜色唯一来源是 ``QPalette``（由 matugen / 系统主题注入）。
本模块不读取外部配色文件，也不在 QSS 里写死十六进制颜色。

约定：
- ``get_theme_colors()`` 负责「调色板 → 语义 token」
- ``MODERN_QSS`` 只使用 token，不直接使用调色板
- ``build_qss()`` 做一次遍历替换，缺失 token 会立即报错
"""

import re

from .qt_compat import QColor

MODERN_QSS = """
/* ================== DMS Material You 主题 ================== */

/* ====== 顶部菜单栏 ====== */
QMenuBar { background-color: {{BG}}; border: none; padding: 4px 8px; }
QMenuBar::item {
    background-color: transparent;
    padding: 6px 14px;
    margin: 2px 4px;
    border-radius: 6px;
    color: {{TEXT}};
}
QMenuBar::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}}; }
QMenuBar::item:selected { background-color: {{ACTIVE_BG}}; color: {{TEXT}}; }

QMainWindow::separator { background-color: {{BG}}; width: 0px; height: 0px; }
QSplitter::handle { background-color: {{BG}}; }

/* ====== 工具栏 ====== */
QToolBar {
    background-color: {{BG}};
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolBar::separator {
    background-color: {{BORDER}};
    width: 1px;
    margin: 4px 6px;
}
QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px;
    margin: 2px;
    color: {{TEXT}};
}
QToolBar QToolButton:hover {
    background-color: {{HOVER_BG}};
}
QToolBar QToolButton:pressed, QToolBar QToolButton:checked {
    background-color: {{PRIMARY_CONTAINER}};
    color: {{ON_PRIMARY_CONTAINER}};
}

/* ====== 弹出菜单 ====== */
QMenu { background-color: {{SURFACE_CONTAINER_HIGH}}; border: 1px solid {{BORDER}}; border-radius: 8px; padding: 6px; outline: none; }
QMenu::item { background-color: transparent; padding: 6px 24px 6px 12px; border-radius: 6px; color: {{TEXT}}; }
QMenu::item:selected { background-color: {{ACTIVE_BG}}; color: {{TEXT}}; }
QMenu::item:disabled { color: {{TEXT_DISABLED}}; background-color: transparent; }
QMenu::separator { height: 1px; background: {{BORDER}}; margin: 4px 8px; }
QMenu QLabel, QMenu QCheckBox, QMenu QRadioButton { color: {{TEXT}}; background: transparent; }

/* ====== 提示气泡 ====== */
QToolTip { background-color: {{SURFACE_CONTAINER_HIGHEST}}; color: {{TEXT}}; border: 1px solid {{BORDER}}; border-radius: 6px; padding: 4px 8px; }

/* ====== 停靠窗口 & 标签页 ====== */
QDockWidget { border: none; margin: 0px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 0px; margin: 0px; }

QTabWidget { border: none; background: {{BG}}; }
QTabWidget::pane { border: none; background: {{BG}}; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

QTabBar { background: transparent; border: none; qproperty-drawBase: 0; }
QTabBar::tab {
    background: transparent; border: none; border-bottom: 2px solid transparent;
    padding: 6px 20px; margin: 4px 4px 0px 4px;
    color: {{ON_SURFACE_VARIANT}};
}
QTabBar::tab:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}}; }
QTabBar::tab:selected { background: transparent; border-bottom: 2px solid {{PRIMARY}}; color: {{PRIMARY}}; }
QTabBar::tab:focus:!selected { background-color: {{FOCUS_BG}}; }

QTabBar::close-button { subcontrol-origin: padding; subcontrol-position: center right; margin-right: 6px; width: 16px; height: 16px; border-radius: 8px; background: transparent; }
QTabBar::close-button:hover { background-color: {{CLOSE_HOVER}}; }

/* ====== 列表 / 树（通用面板：图层、笔刷等） ====== */
QTreeView, QListView, QListWidget { background-color: {{BG}}; border: none; outline: none; show-decoration-selected: 1; }
QTreeView::item, QListView::item, QListWidget::item {
    border-radius: 6px;
    padding: 8px 6px;
    margin: 2px 0px;
    color: {{TEXT}};
}
QTreeView::item:hover:!selected, QListView::item:hover:!selected, QListWidget::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}}; }
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected { background-color: {{PRIMARY_CONTAINER}}; color: {{ON_PRIMARY_CONTAINER}}; }

/* ====== 表头 / 表格 ====== */
QTableView, QTableWidget { background-color: {{BG}}; border: none; gridline-color: {{BORDER}}; }
QHeaderView { background-color: {{BG}}; border: none; }
QHeaderView::section {
    background-color: {{SURFACE_CONTAINER}};
    color: {{TEXT}};
    border: none;
    border-right: 1px solid {{BORDER}};
    border-bottom: 1px solid {{BORDER}};
    padding: 4px 6px;
}
QHeaderView::section:hover { background-color: {{HOVER_BG}}; }
QHeaderView::section:checked { background-color: {{SURFACE_CONTAINER_HIGH}}; }
QTableCornerButton::section { background-color: {{SURFACE_CONTAINER}}; border: none; }

/* ====== 特殊修补：配置窗口左侧（KPageListView 是 QListView 子类） ====== */
QDialog QListView { padding: 0px 6px; }
QDialog QListView::item { border-radius: 6px; padding: 2px 4px; margin: 2px 0px; color: {{TEXT}}; }
QDialog QListView::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}}; }
QDialog QListView::item:selected { background-color: {{PRIMARY_CONTAINER}}; color: {{ON_PRIMARY_CONTAINER}}; }

/* ====== 按钮 ====== */
QPushButton { background-color: {{SURFACE_CONTAINER_HIGH}}; border: none; border-radius: 6px; padding: 5px 12px; color: {{TEXT}}; }
QPushButton:hover { background-color: {{SURFACE_CONTAINER_HIGHEST}}; }
QPushButton:default { background-color: {{PRIMARY}}; color: {{ON_PRIMARY}}; }
QPushButton:default:hover { background-color: {{PRIMARY_HOVER}}; }
QPushButton:pressed { background-color: {{PRIMARY_CONTAINER}}; color: {{ON_PRIMARY_CONTAINER}}; }
QPushButton:default:pressed { background-color: {{PRIMARY_CONTAINER}}; color: {{ON_PRIMARY_CONTAINER}}; }
QPushButton:focus:!pressed:!default { background-color: {{FOCUS_BG}}; }
QPushButton:disabled { color: {{TEXT_DISABLED}}; background-color: {{DISABLED_BG}}; }

/* 键盘焦点：只叠加状态层，不改变控件尺寸 */
QToolBar QToolButton:focus:!checked:!pressed { background-color: {{FOCUS_BG}}; }

/* ====== 输入框 & 下拉框 ====== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, KisDoubleSliderSpinBox, KisSliderSpinBox {
    background-color: {{ITEM_BG}};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 8px;
    color: {{TEXT}};
    selection-background-color: {{SELECT_BG}};
    selection-color: {{HIGHLIGHT_TEXT}};
}
QSpinBox, QDoubleSpinBox { padding-right: 20px; }

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, KisDoubleSliderSpinBox:hover, KisSliderSpinBox:hover {
    background-color: {{HOVER_BG}};
    color: {{TEXT}};
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, KisDoubleSliderSpinBox:focus, KisSliderSpinBox:focus {
    background-color: {{ITEM_BG}};
    color: {{TEXT}};
    border: 1px solid {{SELECT_BG}};
}

QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {
    background: transparent;
    color: {{TEXT}};
    selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}};
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right; width: 16px;
    border-top-right-radius: 4px; background-color: {{ITEM_BG}};
    border-left: 1px solid {{BORDER}}; margin-top: 2px; margin-right: 2px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right; width: 16px;
    border-bottom-right-radius: 4px; background-color: {{ITEM_BG}};
    border-left: 1px solid {{BORDER}}; margin-bottom: 2px; margin-right: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background-color: {{HOVER_BG}}; }

/* 上下箭头：SVG 由 icons.py 按主题色渲染，这里只负责尺寸与位置 */
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: {{SPIN_UP_ICON}};
    width: 9px;
    height: 9px;
    subcontrol-origin: border;
    subcontrol-position: center;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: {{SPIN_DOWN_ICON}};
    width: 9px;
    height: 9px;
    subcontrol-origin: border;
    subcontrol-position: center;
}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
QSpinBox::up-arrow:off, QDoubleSpinBox::up-arrow:off { image: {{SPIN_UP_DISABLED_ICON}}; }
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled,
QSpinBox::down-arrow:off, QDoubleSpinBox::down-arrow:off { image: {{SPIN_DOWN_DISABLED_ICON}}; }

QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background-color: {{SURFACE_CONTAINER_HIGH}}; border: 1px solid {{BORDER}}; border-radius: 6px; selection-background-color: {{PRIMARY_CONTAINER}}; selection-color: {{ON_PRIMARY_CONTAINER}}; color: {{TEXT}}; }

/* ====== 滚动条（横向与竖向统一） ====== */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: {{MID_BG}};
    min-height: 30px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: {{SCROLLBAR_HOVER}};
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: {{MID_BG}};
    min-width: 30px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: {{SCROLLBAR_HOVER}};
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
    width: 0px;
    height: 0px;
}

/* ====== 欢迎页底层兜底 ====== */
KisWelcomePageWidget QFrame,
KisWelcomePageWidget QTextBrowser {
    background-color: transparent;
    border: none;
}

/* ====== 复选框 / 单选按钮 ======
   指示器由 hacks.py 的 IndicatorStyle（QProxyStyle）自绘：
   checkbox 画 M3 圆角方形 + 勾号 / 横杠，radio 画圆环 + 圆点。
   QSS 里不能再写 ::indicator 规则，否则会覆盖掉自绘结果。
   这里只保留文字与间距。 */
QCheckBox, QRadioButton { color: {{TEXT}}; spacing: 6px; }
QCheckBox:disabled, QRadioButton:disabled { color: {{TEXT_DISABLED}}; }
"""

# ---------------------------------------------------------------------------
# 颜色工具
# ---------------------------------------------------------------------------

def _mix(fg, bg, weight):
    """把 fg 按 weight 混到 bg 上（weight=1 → 纯 fg）。"""
    weight = max(0.0, min(1.0, weight))
    return QColor(
        round(fg.red() * weight + bg.red() * (1 - weight)),
        round(fg.green() * weight + bg.green() * (1 - weight)),
        round(fg.blue() * weight + bg.blue() * (1 - weight)),
    )


def _rgba(color, opacity):
    """QSS 用的 rgba 字符串；Qt 的 alpha 是 0-255。"""
    return "rgba({}, {}, {}, {})".format(
        color.red(), color.green(), color.blue(), round(opacity * 255)
    )


def _with_alpha(color, opacity):
    """同色、指定透明度的 QColor（给 QPainter 直接使用）。"""
    result = QColor(color)
    result.setAlphaF(max(0.0, min(1.0, opacity)))
    return result


def _luminance(color):
    """WCAG 相对亮度。"""
    def channel(value):
        value /= 255.0
        return (
            value / 12.92
            if value <= 0.03928
            else ((value + 0.055) / 1.055) ** 2.4
        )

    return (
        0.2126 * channel(color.red())
        + 0.7152 * channel(color.green())
        + 0.0722 * channel(color.blue())
    )


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _text_on(background):
    """在给定背景上选黑或白，取对比度更高的一侧。"""
    black, white = QColor("#000000"), QColor("#ffffff")
    return (
        black
        if _contrast(black, background) >= _contrast(white, background)
        else white
    )


# ---------------------------------------------------------------------------
# 调色板 → 语义色
# ---------------------------------------------------------------------------

def get_theme_colors(palette, color_role, primary=None):
    """把 Krita 当前调色板映射成 M3 语义 token。

    颜色全部来自 QPalette（matugen 注入），这里只做明暗适配与状态层推导：
    - surface / on-surface 来自 Window / WindowText
    - primary 来自 Highlight（或调用方缓存的原始主色）
    - container / outline / 状态层由 primary、on-surface 混合得到

    ``primary`` 用于打破循环：插件会把 ``Highlight`` 改写成
    ``primary-container``（让 delegate 的选中文字色与 QSS 背景一致），
    之后不能再从 ``Highlight`` 反推主色，否则每次刷新都会越变越暗。
    """
    surface = QColor(palette.color(color_role.Window))
    primary = QColor(primary) if primary is not None else QColor(palette.color(color_role.Highlight))


    # 文字优先使用注入的 WindowText；对比度不足时才回退黑/白
    injected_text = QColor(palette.color(color_role.WindowText))
    if _contrast(injected_text, surface) >= 4.5:
        on_surface = injected_text
    else:
        on_surface = _text_on(surface)

    on_primary = _text_on(primary)

    on_surface_variant = _mix(on_surface, surface, 0.70)
    outline = _mix(on_surface, surface, 0.50)
    outline_variant = _mix(on_surface, surface, 0.16)

    surface_container = _mix(on_surface, surface, 0.04)
    surface_container_high = _mix(on_surface, surface, 0.08)
    surface_container_highest = _mix(on_surface, surface, 0.12)

    primary_container = _mix(primary, surface, 0.16)
    on_primary_container = _mix(primary, on_surface, 0.45)
    if _contrast(on_primary_container, primary_container) < 4.5:
        on_primary_container = on_surface

    disabled_text = _mix(on_surface, surface, 0.38)
    scrollbar_thumb = _mix(on_surface, surface, 0.45)
    scrollbar_hover = _mix(on_surface, surface, 0.62)

    return {
        # ---- M3 语义角色 ----
        "SURFACE": surface.name(),
        "SURFACE_CONTAINER": surface_container.name(),
        "SURFACE_CONTAINER_HIGH": surface_container_high.name(),
        "SURFACE_CONTAINER_HIGHEST": surface_container_highest.name(),
        "ON_SURFACE": on_surface.name(),
        "ON_SURFACE_VARIANT": on_surface_variant.name(),
        "OUTLINE": outline.name(),
        "OUTLINE_VARIANT": outline_variant.name(),
        "PRIMARY": primary.name(),
        "ON_PRIMARY": on_primary.name(),
        "PRIMARY_CONTAINER": primary_container.name(),
        "ON_PRIMARY_CONTAINER": on_primary_container.name(),

        # ---- 现有 QSS / 补丁使用的兼容 token ----
        "BG": surface.name(),
        "MID_BG": scrollbar_thumb.name(),
        "ITEM_BG": _rgba(on_surface, 0.06),
        "TEXT": on_surface.name(),
        "TEXT_DISABLED": disabled_text.name(),
        "HOVER_BG": _rgba(on_surface, 0.08),
        "SELECT_BG": primary.name(),
        "HIGHLIGHT_TEXT": on_primary.name(),
        "BORDER": outline_variant.name(),
        "DISABLED_BG": _rgba(on_surface, 0.12),
        "FOCUS_BG": _rgba(primary, 0.10),
        "CLOSE_HOVER": _rgba(on_surface, 0.12),
        "SCROLLBAR_HOVER": scrollbar_hover.name(),
        "ACTIVE_BG": _rgba(on_surface, 0.12),
        "PRIMARY_HOVER": _mix(on_surface, primary, 0.08).name(),
    }


def get_indicator_colors(colors):
    """自绘勾选控件（IndicatorStyle）需要的 QColor 集合。

    M3 语义：checkbox 用 primary 填充 + on-primary 勾号，radio 用 primary
    圆环 + 圆点；禁用态降为 12% 容器 / 38% 前景区分。
    这里把 QSS 用的字符串 token 换成 QColor，颜色推导仍留在本模块。
    """
    primary = QColor(colors["PRIMARY"])
    on_surface = QColor(colors["ON_SURFACE"])
    surface = QColor(colors["SURFACE"])

    return {
        "primary": primary,
        "on_primary": QColor(colors["ON_PRIMARY"]),
        "outline": QColor(colors["OUTLINE"]),
        "hover": _with_alpha(primary, 0.08),
        "disabled_outline": QColor(colors["TEXT_DISABLED"]),
        "disabled_fill": _mix(on_surface, surface, 0.12),
        "disabled_mark": QColor(colors["TEXT_DISABLED"]),
    }


# ---------------------------------------------------------------------------
# 组装
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")


def build_qss(colors, icons=None):
    """单次遍历替换 token。

    比链式 ``str.replace`` 少扫描 9 遍模板；拼错的 token 会直接 KeyError，
    不会把 ``{{XXX}}`` 静默漏进样式表。

    ``icons`` 由 ``icons.prepare_icons()`` 提供（``SPIN_UP_ICON`` 等），
    与语义色一起参与替换。
    """
    tokens = {**colors, **icons} if icons else colors
    return _TOKEN_RE.sub(lambda match: tokens[match.group(1)], MODERN_QSS)


__all__ = [
    "MODERN_QSS",
    "get_theme_colors",
    "get_indicator_colors",
    "build_qss",
]