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
from html import unescape

from .qt_compat import (
    ANTIALIASING,
    COLOR_ROLE,
    FRAMELESS_WINDOW_HINT,
    NO_BRUSH,
    NO_DROP_SHADOW_WINDOW_HINT,
    NO_PEN,
    PIXEL_METRIC,
    POINTING_HAND,
    POLISH_EVENT,
    PRIMITIVE_ELEMENT,
    ROUND_CAP,
    ROUND_JOIN,
    SHOW_EVENT,
    SIZE_POLICY,
    STATE_FLAG,
    STRONG_FOCUS,
    TEXT_BESIDE_ICON,
    WA_TRANSLUCENT_BACKGROUND,
    QApplication,
    QCheckBox,
    QDesktopServices,
    QDialog,
    QDoubleSpinBox,
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
    QSize,
    QToolButton,
    QUrl,
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


_LINK_RE = re.compile(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")

# 社区资源：图标按钮与链接标签成对出现（名字来自 KisWelcomePage.ui）
_WELCOME_ROWS = (
    ("userManualIcon", "manualLink"),
    ("supportKritaIcon", "supportKritaLink"),
    ("kdeIcon", "poweredByKDELink"),
    ("sourceCodeIcon", "sourceCodeLink"),
    ("gettingStartedIcon", "gettingStartedLink"),
    ("userCommunityIcon", "userCommunityLink"),
    ("kritaWebsiteIcon", "kritaWebsiteLink"),
)

# Krita 会往这些标题里写自己的混合色，这里统一换回 on-surface
_WELCOME_TITLES = (
    "startTitleLabel",
    "helpTitleLabel",
    "recentDocumentsLabel",
    "newsTitleLabel",
)


def _link_parts(html):
    """从 Krita 生成的 ``<a href=...>文字</a>`` 中取出地址和纯文字。"""
    html = html or ""
    match = _LINK_RE.search(html)
    if match is None:
        return "", _TAG_RE.sub("", html).strip()
    text = unescape(_TAG_RE.sub("", match.group(2))).strip()
    return match.group(1), text


def _row_layout(widget):
    """找到直接容纳 ``widget`` 的那个布局。

    社区资源每一行是 ``QHBoxLayout``：图标按钮和链接标签是两个 item，
    没有包裹用的 QWidget。从父控件的布局往下递归，找到真正持有它的那个。
    """
    parent = widget.parentWidget()
    if parent is None:
        return None

    def search(layout):
        if layout is None:
            return None
        if layout.indexOf(widget) >= 0:
            return layout
        for index in range(layout.count()):
            found = search(layout.itemAt(index).layout())
            if found is not None:
                return found
        return None

    return search(parent.layout())


def _open_welcome_link(button):
    """点击整行时用系统默认程序打开当前 href。"""
    url = button.property("dmsHref")
    if url:
        QDesktopServices.openUrl(QUrl(url))


def _restyle(widget, qss):
    """只在样式真正变化时写入，避免反复 polish 整个欢迎页。

    比较控件当前样式表，而不是记在 property 里：Krita 的
    ``slotUpdateThemeColors()`` 会用自己的混合色覆盖 ``newFileLink`` 等
    控件的样式，直接对比才能在下一次补丁时重新夺回控制权。
    """
    if widget.styleSheet() == qss:
        return
    widget.setStyleSheet(qss)


def patch_welcome_page(qwin, colors):
    """把 Krita 欢迎页改成统一的 M3 行式交互。

    - 社区资源：每行合成一个 ``QToolButton``（图标 + 文字），整行可点击，
      hover / 按下都有状态层，不再有下划线。原来的图标按钮和链接标签
      只隐藏、不销毁，Krita 更新文字或图标时不会崩。
    - 开始创作：两张 tonal 卡片，图标缩到 28px，去掉下划线。
    - ``devBuildLabel`` 保持 Krita 原样（“正在运行测试版本”的链接与下划线不动）。
    """
    row_qss = f"""
        QToolButton {{
            background-color: {colors['ITEM_BG']};
            color: {colors['TEXT']};
            border: none;
            border-radius: 8px;
            padding: 5px 14px 5px 8px;
        }}
        QToolButton:hover {{ background-color: {colors['ACTIVE_BG']}; }}
        QToolButton:pressed {{
            background-color: {colors['PRIMARY_CONTAINER']};
            color: {colors['ON_PRIMARY_CONTAINER']};
        }}
        QToolButton:focus {{ background-color: {colors['FOCUS_BG']}; }}
    """
    file_qss = f"""
        QToolButton {{
            background-color: {colors['SURFACE_CONTAINER_HIGH']};
            color: {colors['TEXT']};
            border: none;
            border-radius: 12px;
            padding: 10px 18px 10px 12px;
        }}
        QToolButton:hover {{ background-color: {colors['SURFACE_CONTAINER_HIGHEST']}; }}
        QToolButton:pressed {{
            background-color: {colors['PRIMARY_CONTAINER']};
            color: {colors['ON_PRIMARY_CONTAINER']};
        }}
        QToolButton:focus {{ background-color: {colors['FOCUS_BG']}; }}
    """

    for icon_name, label_name in _WELCOME_ROWS:
        icon = qwin.findChild(QWidget, icon_name)
        label = qwin.findChild(QLabel, label_name)
        if icon is None or label is None:
            continue

        href, text = _link_parts(label.text())
        button = qwin.findChild(QToolButton, "dmsRow_" + icon_name)

        if button is None:
            layout = _row_layout(icon)
            if layout is None:
                continue
            # 先记录可见性：接下来我们就把原控件藏起来了
            visible = not icon.isHidden() and not label.isHidden()
            button = QToolButton(qwin)
            button.setObjectName("dmsRow_" + icon_name)
            button.setToolButtonStyle(TEXT_BESIDE_ICON)
            button.setCursor(POINTING_HAND)
            button.setFocusPolicy(STRONG_FOCUS)
            button.setSizePolicy(SIZE_POLICY.Minimum, SIZE_POLICY.Fixed)
            button.setIconSize(QSize(24, 24))
            button.setVisible(visible)
            button.clicked.connect(lambda _=False, b=button: _open_welcome_link(b))
            layout.insertWidget(layout.indexOf(icon), button)
            # 原控件保留在对象树里，Krita 的 retranslate / 图标更新还能写它们
            layout.removeWidget(icon)
            layout.removeWidget(label)
            icon.hide()
            label.hide()

        button.setProperty("dmsHref", href)
        # 末尾的 ↗ 是“会在浏览器里打开”的固定提示，不依赖 hover
        button.setText(text.replace("&", "&&") + "  ↗")
        button.setToolTip(href)
        button.setAccessibleName(text)
        button.setIcon(icon.icon())
        _restyle(button, row_qss)

    for name, shortcut_name in (
        ("newFileLink", "newFileLinkShortcut"),
        ("openFileLink", "openFileShortcut"),
    ):
        button = qwin.findChild(QToolButton, name)
        if button is None:
            continue
        button.setIconSize(QSize(28, 28))
        font = button.font()
        font.setUnderline(False)
        button.setFont(font)
        _restyle(button, file_qss)

        # 快捷键提示保留下来，正好当作“可以打开本地文件”的线索
        shortcut = qwin.findChild(QLabel, shortcut_name)
        if shortcut is not None:
            _restyle(
                shortcut,
                f"color: {colors['ON_SURFACE_VARIANT']}; background: transparent;",
            )

    for name in _WELCOME_TITLES:
        title = qwin.findChild(QLabel, name)
        if title is not None:
            _restyle(title, f"color: {colors['TEXT']}; background: transparent;")

    clear_button = qwin.findChild(QWidget, "clearRecentFilesLink")
    if clear_button is not None:
        _restyle(
            clear_button,
            f"""
            QPushButton {{
                background: transparent;
                color: {colors['PRIMARY']};
                border: none;
                border-radius: 8px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{ background-color: {colors['HOVER_BG']}; }}
            QPushButton:pressed {{
                background-color: {colors['PRIMARY_CONTAINER']};
                color: {colors['ON_PRIMARY_CONTAINER']};
            }}
            """,
        )

    news_options = qwin.findChild(QToolButton, "btnNewsOptions")
    if news_options is not None:
        _restyle(
            news_options,
            f"""
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }}
            QToolButton:hover {{ background-color: {colors['HOVER_BG']}; }}
            QToolButton:pressed {{
                background-color: {colors['PRIMARY_CONTAINER']};
            }}
            """,
        )

    # 最近图像 / 最新资讯两块面板：统一成 M3 细描边
    for name in ("recentDocsStackedWidget", "newsFrame"):
        frame = qwin.findChild(QWidget, name)
        if frame is not None:
            _restyle(
                frame,
                f"#{name} {{ border: 1px solid {colors['OUTLINE_VARIANT']};"
                f" border-radius: 12px; background: transparent; }}",
            )

    recent_list = qwin.findChild(QListWidget, "recentDocumentsListView")
    if recent_list is not None:
        _restyle(
            recent_list,
            f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{
                color: {colors['TEXT']};
                border-radius: 6px;
                padding: 2px;
            }}
            QListWidget::item:hover {{ background-color: {colors['HOVER_BG']}; }}
            QListWidget::item:selected {{
                background-color: {colors['PRIMARY_CONTAINER']};
                color: {colors['ON_PRIMARY_CONTAINER']};
            }}
            """,
        )


def patch_angle_spinbox(qwin):
    """给画布角度框打上 objectName，让 QSS 的 ID 选择器收紧 padding。

    状态栏里的 ``KisAngleSelectorSpinBox`` 最小高度由 Krita 自己计算
    （约 24px），而且它会在 hover / focus 时重写这个控件的 widget
    stylesheet，普通类型选择器会被覆盖。ID 选择器的优先级更高，
    可以在所有状态下生效，避免数字被上下裁掉。
    """
    for spin in qwin.findChildren(QDoubleSpinBox):
        if spin.objectName() == "dmsAngleSpin":
            continue
        if spin.metaObject().className() != "KisAngleSelectorSpinBox":
            continue
        spin.setObjectName("dmsAngleSpin")
        # 重新套一次自身的 widget stylesheet：qobject 的 objectName 变化
        # 不会自动让应用级 QSS 按新 ID 重新匹配，重置样式表可以强制刷新。
        sheet = spin.styleSheet()
        spin.setStyleSheet(sheet if sheet else "QDoubleSpinBox{}")


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