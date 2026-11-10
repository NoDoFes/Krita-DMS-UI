"""DMS Modern UI 插件入口。

只做三件事：
1. 装配全局过滤器与菜单动画
2. 把调色板（matugen 注入）应用到全局 QSS / QPalette
3. 调度窗口级补丁（欢迎页、菜单文本、菜单显隐）

具体样式在 ``styles.py``，窗口补丁在 ``hacks.py``，
设置菜单在 ``settings_ui.py``，动画在 ``menu_animation.py``。
"""

from krita import Krita, Extension

from .qt_compat import COLOR_GROUP, COLOR_ROLE, QApplication, QColor, QTimer
from .styles import build_qss, get_theme_colors
from .hacks import MenuFilter, patch_welcome_page
from .menu_animation import MenuAnimator
from .settings_ui import (
    SETTING_MENU_ANIMATION,
    apply_menu_text_settings,
    apply_menu_visibility_settings,
    read_bool_setting,
    setup_ui_settings,
)


class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.menu_filter = None
        self.menu_animator = None
        self._dms_menu = None

    def setup(self):
        pass

    def start(self):
        self._install_menu_filter()
        self._install_menu_animator()

        # 启动时只注入一次全局 QSS（很快，避免拖慢启动）
        self.apply_global_theme()

        # 欢迎页 / 菜单文本等窗口级操作延迟 1 秒
        QTimer.singleShot(1000, self.apply_heavy_hacks)

        # 新窗口创建后重新套用窗口级补丁
        Krita.instance().notifier().windowCreated.connect(self.apply_heavy_hacks)

    # ---- 装配 ----------------------------------------------------------

    def _install_menu_filter(self):
        if self.menu_filter is not None or self.app is None:
            return
        self.menu_filter = MenuFilter(self.app)
        self.app.installEventFilter(self.menu_filter)

    def _install_menu_animator(self):
        if self.menu_animator is not None or self.app is None:
            return
        self.menu_animator = MenuAnimator(self.app)
        enabled = read_bool_setting(SETTING_MENU_ANIMATION, default=True)
        self.menu_animator.set_enabled(enabled)
        self.menu_animator.install()

    # ---- 主题 ----------------------------------------------------------

    def theme_colors(self):
        """当前调色板对应的语义色：QSS 与窗口补丁共用同一份。"""
        if self.app is None:
            return None
        return get_theme_colors(self.app.palette(), COLOR_ROLE)

    def apply_global_theme(self):
        """只调一次 setStyleSheet，瞬间生效。"""
        colors = self.theme_colors()
        if colors is None:
            return

        self.app.setStyleSheet(build_qss(colors))

        # 只同步高亮色，文字色交给 matugen 注入的调色板
        pal = self.app.palette()
        pal.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
        pal.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))

        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.WindowText, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.Text, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.ButtonText, QColor(colors["TEXT_DISABLED"]))
        self.app.setPalette(pal)

    def refresh_theme(self):
        """重载主题：QSS、调色板、已打开窗口的补丁一次刷新。"""
        self.apply_global_theme()
        self.apply_heavy_hacks()

    def apply_heavy_hacks(self, *_):
        """窗口级操作：带防重复检查，可被定时器和信号重复调用。"""
        colors = self.theme_colors()
        if colors is None:
            return

        for win in Krita.instance().windows():
            qwin = win.qwindow()
            patch_welcome_page(qwin, colors)
            apply_menu_text_settings(qwin)
            apply_menu_visibility_settings(qwin)

    def createActions(self, window):
        # 只在这里挂载 DMS UI 菜单，不触发全局重绘
        setup_ui_settings(window, self)


instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()
