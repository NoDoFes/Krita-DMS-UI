"""对 Krita 自身硬编码样式的补丁。

包含两部分，互不依赖：
- ``patch_welcome_page``：欢迎页按钮 / 最近文件 / 社区链接
- ``MenuFilter``：去掉 QMenu 黑边，并修复内嵌控件文字消失

本模块只消费 ``styles.get_theme_colors()`` 产出的 token，不自己决定配色。
"""

import re

from .qt_compat import (
    COLOR_ROLE,
    FRAMELESS_WINDOW_HINT,
    NO_DROP_SHADOW_WINDOW_HINT,
    POLISH_EVENT,
    QApplication,
    QCheckBox,
    QLabel,
    QListWidget,
    QMenu,
    QObject,
    QRadioButton,
    QWidget,
    WA_HOVER,
    WA_STYLED_BACKGROUND,
    WA_TRANSLUCENT_BACKGROUND,
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
    """全局事件过滤器：去黑边 + 修复内嵌菜单文字消失。

    只在 ``QMenu`` 的 Polish 事件上工作，其余事件立即返回。
    """

    def __init__(self, app=None):
        super().__init__(app)
        self.app = app
        self._palette_key = None
        self._window_text = None

    def eventFilter(self, obj, event):
        if event.type() != POLISH_EVENT or not isinstance(obj, QMenu):
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