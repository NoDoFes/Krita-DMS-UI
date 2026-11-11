"""对 Krita 自身硬编码样式的补丁。

包含四部分，互不依赖：
- ``patch_welcome_page``：欢迎页按钮 / 最近文件 / 社区链接
- ``MenuFilter``：去掉 QMenu 黑边、修复内嵌控件文字，并让 KPageDialog
  在显示时继承当前应用调色板
- ``inherit_app_palette``：把 QSS 用的同一份调色板套到配置对话框上
- ``IndicatorStyle`` / ``ensure_indicator_style``：用 QProxyStyle 自绘
  checkbox / radio 的 M3 指示器（QSS 画不出勾号与圆点）

本模块只消费 ``styles`` 产出的 token，不自己决定配色。
"""

import re

from .qt_compat import (
    ANTIALIASING,
    COLOR_ROLE,
    FRAMELESS_WINDOW_HINT,
    NO_BRUSH,
    NO_DROP_SHADOW_WINDOW_HINT,
    NO_PEN,
    PIXEL_METRIC,
    POLISH_EVENT,
    PRIMITIVE_ELEMENT,
    QApplication,
    QCheckBox,
    QDialog,
    QLabel,
    QListView,
    QListWidget,
    QMenu,
    QObject,
    QPainterPath,
    QPen,
    QPointF,
    QProxyStyle,
    QRadioButton,
    QRectF,
    ROUND_CAP,
    ROUND_JOIN,
    SHOW_EVENT,
    STATE_FLAG,
    WA_HOVER,
    WA_STYLED_BACKGROUND,
    WA_TRANSLUCENT_BACKGROUND,
    QWidget,
    sip,
)
from .styles import get_indicator_colors


def inherit_app_palette(widget, app=None):
    """把当前应用调色板套到 KPageDialog（配置对话框）上。

    Krita 的画布窗口会用 ``.colors`` 重新构建一份调色板，并可能通过
    ``setPalette()`` 快照到父窗口。QDialog 默认从父窗口继承调色板，
    于是会拿到 matugen 原始的 ``HighlightedText``（深蓝），而 QSS 画的
    选中背景仍是 ``primary-container``，对比度约 1:1。

    QSS 无法覆盖 KDE delegate 的文字色，所以在对话框显示时显式套用
    ``qApp.palette()``。侧栏 ``KPageListView`` 可能在对话框构造时就已经
    解析过调色板，单靠父级传播不一定能刷新，所以对它单独补一次。
    只在颜色真的漂移时调用 ``setPalette``，避免重复 polish。
    """
    if not widget.inherits("KPageDialog"):
        return False

    app = app or QApplication.instance()
    if app is None:
        return False

    palette = app.palette()
    key = palette.cacheKey()
    theme_changed = widget.property("dms_app_palette_key") != key
    if theme_changed:
        widget.setProperty("dms_app_palette_key", key)

    changed = False
    for target in (widget, *widget.findChildren(QListView)):
        if theme_changed or _selection_drifted(target, palette):
            target.setPalette(palette)
            changed = True
    return changed


def _selection_drifted(widget, palette):
    """选中态两个角色是否与应用调色板不一致。"""
    current = widget.palette()
    return (
        current.color(COLOR_ROLE.Highlight) != palette.color(COLOR_ROLE.Highlight)
        or current.color(COLOR_ROLE.HighlightedText)
        != palette.color(COLOR_ROLE.HighlightedText)
    )


def _welcome_signature(colors):
    """欢迎页补丁的缓存键：覆盖所有会用到的颜色。"""
    keys = (
        "ITEM_BG",
        "SURFACE_CONTAINER_HIGH",
        "SURFACE_CONTAINER_HIGHEST",
        "TEXT",
        "HOVER_BG",
        "PRIMARY_CONTAINER",
        "ON_PRIMARY_CONTAINER",
    )
    return "|".join(colors[key] for key in keys)


def patch_welcome_page(qwin, colors):
    """修复 Krita 欢迎页 C++ 写死的样式"""
    signature = _welcome_signature(colors)
    if qwin.property("dms_welcome_signature") == signature:
        return
    qwin.setProperty("dms_welcome_signature", signature)

    new_file_btn = qwin.findChild(QWidget, "newFileLink")
    open_file_btn = qwin.findChild(QWidget, "openFileLink")
    recent_list = qwin.findChild(QListWidget, "recentDocumentsListView")

    if new_file_btn or open_file_btn:
        btn_qss = f"""
            QWidget {{
                background-color: {colors['SURFACE_CONTAINER_HIGH']};
                border-radius: 6px;
                color: {colors['TEXT']};
                padding: 8px 12px;
            }}
            QWidget:hover {{ background-color: {colors['SURFACE_CONTAINER_HIGHEST']}; }}
            QWidget:pressed {{ background-color: {colors['PRIMARY_CONTAINER']}; color: {colors['ON_PRIMARY_CONTAINER']}; }}
        """
        for btn in [new_file_btn, open_file_btn]:
            if btn:
                btn.setStyleSheet(btn_qss)
                for lbl in btn.findChildren(QLabel):
                    text = lbl.text()
                    if not text: continue
                    if "Ctrl" in text or "Alt" in text:
                        lbl.hide()
                        lbl.setFixedWidth(0)
                        continue
                    clean_text = re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', text).strip()
                    if text != clean_text:
                        lbl.setText(clean_text)
                    lbl.setStyleSheet(f"text-decoration: none; color: {colors['TEXT']}; background: transparent;")

    if recent_list:
        recent_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{ color: {colors['TEXT']}; border-radius: 6px; padding: 2px; }}
            QListWidget::item:hover {{ background-color: {colors['HOVER_BG']}; }}
            QListWidget::item:selected {{ background-color: {colors['PRIMARY_CONTAINER']}; color: {colors['ON_PRIMARY_CONTAINER']}; }}
        """)

    keywords = ["使用手册", "捐款支持", "KDE 社区", "源代码库", "新手入门", "用户社区", "官方网站"]
    for widget in qwin.findChildren(QWidget):
        try:
            if not widget.isVisible(): continue
            text = ""
            if hasattr(widget, "text") and callable(widget.text):
                text = widget.text()

            if text and any(kw in text for kw in keywords):
                if widget.property("dms_link_signature") == signature:
                    continue
                widget.setProperty("dms_link_signature", signature)

                clean_text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text, flags=re.DOTALL)
                clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)

                if hasattr(widget, "setText") and widget.text() != clean_text:
                    widget.setText(clean_text)

                widget.setAttribute(WA_HOVER, True)

                widget.setStyleSheet(f"""
                    QLabel {{
                        background-color: {colors['ITEM_BG']};
                        border-radius: 6px;
                        padding: 6px 12px;
                        margin: 2px 0px;
                        color: {colors['TEXT']};
                    }}
                    QLabel:hover {{
                        background-color: {colors['HOVER_BG']};
                    }}
                """)

                parent = widget.parentWidget()
                while parent and parent != qwin:
                    # 【核心修复】限制最大宽度和高度，防止涂色到整个左侧大容器
                    if 100 < parent.width() < 350 and 25 < parent.height() < 60:
                        parent.setAttribute(WA_STYLED_BACKGROUND, True)

                        parent.setStyleSheet(f"""
                            QWidget {{
                                background-color: {colors['ITEM_BG']};
                                border-radius: 6px;
                                padding: 4px 8px;
                                margin: 2px 0px;
                            }}
                            QWidget:hover {{
                                background-color: {colors['HOVER_BG']};
                            }}
                            QLabel {{
                                background: transparent;
                                color: {colors['TEXT']};
                                text-decoration: none;
                            }}
                        """)
                        break
                    parent = parent.parentWidget()
        except Exception:
            pass

class MenuFilter(QObject):
    """全局事件过滤器：去黑边 + 修复内嵌菜单文字 + 配置对话框调色板。

    只关心两类低频事件：``QMenu`` 的 Polish，以及 ``KPageDialog`` 的 Show。
    其余事件只做一次整数比较就返回。
    """

    def __init__(self, app=None):
        super().__init__(app)
        self.app = app
        self._palette_key = None
        self._window_text = None

    def eventFilter(self, obj, event):
        etype = event.type()

        if etype == SHOW_EVENT:
            if isinstance(obj, QDialog):
                inherit_app_palette(obj, self.app)
            return False

        if etype != POLISH_EVENT or not isinstance(obj, QMenu):
            return False

        self._fix_window_chrome(obj)
        self._restore_embedded_text(obj)
        return False

    # ---- 去黑边 --------------------------------------------------------

    @staticmethod
    def _fix_window_chrome(menu):
        if menu.property("dms_polished"):
            return
        menu.setProperty("dms_polished", True)
        menu.setWindowFlags(
            menu.windowFlags()
            | FRAMELESS_WINDOW_HINT
            | NO_DROP_SHADOW_WINDOW_HINT
        )
        menu.setAttribute(WA_TRANSLUCENT_BACKGROUND, True)

    # ---- 内嵌控件文字 --------------------------------------------------

    def _restore_embedded_text(self, menu):
        text_color = self._window_text_color()
        if text_color is None:
            return

        for action in menu.actions():
            if not hasattr(action, "defaultWidget"):
                continue
            widget = action.defaultWidget()
            if widget is None:
                continue
            for child in (widget, *widget.findChildren(QWidget)):
                if not isinstance(child, (QLabel, QCheckBox, QRadioButton)):
                    continue
                # 颜色没变就不重复 setStyleSheet（会触发重新 polish）
                if child.property("dms_menu_text_color") == text_color:
                    continue
                child.setProperty("dms_menu_text_color", text_color)
                child.setStyleSheet(
                    f"color: {text_color}; background: transparent;"
                )

    def _window_text_color(self):
        """缓存调色板文字色，避免每个菜单、每个 action 重复取色。"""
        app = self.app or QApplication.instance()
        if app is None:
            return None

        palette = app.palette()
        key = palette.cacheKey()
        if key != self._palette_key:
            self._palette_key = key
            self._window_text = palette.color(COLOR_ROLE.WindowText).name()
        return self._window_text


# ---------------------------------------------------------------------------
# 勾选控件：M3 指示器自绘
# ---------------------------------------------------------------------------

# M3 尺寸是按触屏 dp 定的，桌面绘图软件按像素收紧：18px 视觉尺寸、
# 2px 描边、约 3px 圆角，行高基本不变。
_CHECK_SIZE = 18
_ITEM_CHECK_SIZE = 14
_BORDER = 2.0
_RADIUS_RATIO = 0.18

_SIZE_METRICS = (
    PIXEL_METRIC.PM_IndicatorWidth,
    PIXEL_METRIC.PM_IndicatorHeight,
    PIXEL_METRIC.PM_ExclusiveIndicatorWidth,
    PIXEL_METRIC.PM_ExclusiveIndicatorHeight,
)

# 已安装的样式对象。Qt 换样式时会删除旧对象，用 sip.isdeleted 判断存活，
# 避免重复包裹（带样式表时 app.style() 返回的是内部 QStyleSheetStyle 包装，
# 不能靠 isinstance 判断）。
_installed_style = None


def _centered_square(rect, size):
    """在 rect 里取居中的正方形，避免指示器被拉成长方形。"""
    side = float(min(size, rect.width(), rect.height()))
    return QRectF(
        rect.x() + (rect.width() - side) / 2.0,
        rect.y() + (rect.height() - side) / 2.0,
        side,
        side,
    )


class IndicatorStyle(QProxyStyle):
    """用 QPainter 画 M3 的 checkbox / radio 指示器。

    - checkbox：圆角方形；选中 = primary 填充 + on-primary 勾号，
      部分选中 = 横杠，未选中 = outline 描边 + 8% primary 悬停层
    - radio：圆形；选中 = primary 圆环 + 圆点，未选中 = outline 圆环
    - 项视图勾选（图层 / 列表）复用同一套画法，尺寸小一号

    只覆写 ``pixelMetric`` 与 ``drawPrimitive``，未命中的图元原样交给底层
    样式。颜色由 ``ensure_indicator_style()`` 注入，主题切换只更新颜色，
    不重建样式对象。
    """

    CHECK_SIZE = _CHECK_SIZE
    ITEM_CHECK_SIZE = _ITEM_CHECK_SIZE

    def __init__(self, base, colors):
        super().__init__(base)
        self._colors = get_indicator_colors(colors)

    def set_theme(self, colors):
        self._colors = get_indicator_colors(colors)

    # ---- 尺寸 ----------------------------------------------------------

    def pixelMetric(self, metric, option=None, widget=None):
        if metric in _SIZE_METRICS:
            return self.CHECK_SIZE
        return super().pixelMetric(metric, option, widget)

    # ---- 绘制 ----------------------------------------------------------

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == PRIMITIVE_ELEMENT.PE_IndicatorCheckBox:
            self._draw_check(painter, option, self.CHECK_SIZE)
            return
        if element == PRIMITIVE_ELEMENT.PE_IndicatorItemViewItemCheck:
            self._draw_check(painter, option, self.ITEM_CHECK_SIZE)
            return
        if element == PRIMITIVE_ELEMENT.PE_IndicatorRadioButton:
            self._draw_radio(painter, option)
            return
        super().drawPrimitive(element, option, painter, widget)

    def _draw_check(self, painter, option, size):
        colors = self._colors
        state = option.state
        enabled = bool(state & STATE_FLAG.State_Enabled)
        checked = bool(state & STATE_FLAG.State_On)
        partial = bool(state & STATE_FLAG.State_NoChange)
        hovered = enabled and bool(state & STATE_FLAG.State_MouseOver)

        box = _centered_square(option.rect, size)
        border = min(_BORDER, size / 4.0)
        radius = max(2.0, size * _RADIUS_RATIO)

        if checked or partial:
            fill = colors["primary"] if enabled else colors["disabled_fill"]
            edge = fill
            mark = colors["on_primary"] if enabled else colors["disabled_mark"]
        else:
            fill = colors["hover"] if hovered else None
            edge = colors["outline"] if enabled else colors["disabled_outline"]
            mark = None

        painter.save()
        painter.setRenderHint(ANTIALIASING, True)

        if fill is not None:
            painter.setPen(NO_PEN)
            painter.setBrush(fill)
            painter.drawRoundedRect(box, radius, radius)

        painter.setPen(QPen(edge, border))
        painter.setBrush(NO_BRUSH)
        inner = box.adjusted(border / 2, border / 2, -border / 2, -border / 2)
        inner_radius = max(1.0, radius - border / 2)
        painter.drawRoundedRect(inner, inner_radius, inner_radius)

        if mark is not None:
            pen = QPen(mark, max(1.6, size * 0.12))
            pen.setCapStyle(ROUND_CAP)
            pen.setJoinStyle(ROUND_JOIN)
            painter.setPen(pen)
            if checked:
                path = QPainterPath()
                path.moveTo(box.left() + box.width() * 0.26, box.top() + box.height() * 0.53)
                path.lineTo(box.left() + box.width() * 0.43, box.top() + box.height() * 0.70)
                path.lineTo(box.left() + box.width() * 0.75, box.top() + box.height() * 0.33)
                painter.drawPath(path)
            else:
                middle = box.center().y()
                painter.drawLine(
                    QPointF(box.left() + box.width() * 0.28, middle),
                    QPointF(box.left() + box.width() * 0.72, middle),
                )

        painter.restore()

    def _draw_radio(self, painter, option):
        colors = self._colors
        state = option.state
        enabled = bool(state & STATE_FLAG.State_Enabled)
        checked = bool(state & STATE_FLAG.State_On)
        hovered = enabled and bool(state & STATE_FLAG.State_MouseOver)

        box = _centered_square(option.rect, self.CHECK_SIZE)
        border = min(_BORDER, box.width() / 4.0)
        inner = box.adjusted(border / 2, border / 2, -border / 2, -border / 2)

        if checked:
            edge = colors["primary"] if enabled else colors["disabled_outline"]
            fill = None
            dot = edge
        else:
            edge = colors["outline"] if enabled else colors["disabled_outline"]
            fill = colors["hover"] if hovered else None
            dot = None

        painter.save()
        painter.setRenderHint(ANTIALIASING, True)

        if fill is not None:
            painter.setPen(NO_PEN)
            painter.setBrush(fill)
            painter.drawEllipse(inner)

        painter.setPen(QPen(edge, border))
        painter.setBrush(NO_BRUSH)
        painter.drawEllipse(inner)

        if dot is not None:
            radius = inner.width() * 0.24  # 直径约为圆环内径的一半（M3 比例）
            painter.setPen(NO_PEN)
            painter.setBrush(dot)
            painter.drawEllipse(inner.center(), radius, radius)

        painter.restore()


def ensure_indicator_style(colors, app=None):
    """确保自绘指示器已生效（幂等）。

    Krita 的样式菜单会调用 ``QApplication.setStyle()``，把我们包在
    ``QStyleSheetStyle`` 里的代理样式一起换掉，所以每次应用主题 / 窗口
    补丁时都检查一次：旧对象已被 Qt 销毁就重新包裹当前样式，否则只更新
    颜色。
    """
    global _installed_style

    app = app or QApplication.instance()
    if app is None or colors is None:
        return False

    if _installed_style is not None and not sip.isdeleted(_installed_style):
        _installed_style.set_theme(colors)
        return False

    _installed_style = IndicatorStyle(app.style(), colors)
    app.setStyle(_installed_style)
    return True