"""DMS Modern UI 插件入口。

只做三件事：
1. 装配全局过滤器与菜单动画
2. 把调色板（matugen 注入）应用到全局 QSS / QPalette
3. 调度窗口级补丁（欢迎页、菜单文本、菜单显隐）

具体样式在 ``styles.py``，窗口补丁在 ``hacks.py``，
设置菜单在 ``settings_ui.py``，动画在 ``menu_animation.py``。
"""

__version__ = "1.0"

from krita import Extension, Krita

from .hacks import (
    MenuFilter,
    ensure_indicator_style,
    inherit_app_palette,
    patch_angle_spinbox,
    patch_layer_editor,
    patch_welcome_page,
)
from .icons import prepare_icons
from .menu_animation import MenuAnimator
from .qt_compat import COLOR_GROUP, COLOR_ROLE, QApplication, QColor, QTimer
from .settings_ui import (
    SETTING_MENU_ANIMATION,
    apply_menu_text_settings,
    apply_menu_visibility_settings,
    read_bool_setting,
    setup_ui_settings,
)
from .styles import build_qss, get_theme_colors
from .theme_watcher import ThemeWatcher


class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.menu_filter = None
        self.menu_animator = None
        self.theme_watcher = None
        self._dms_menu = None
        # matugen 注入的原始主色；与插件改写后的 Highlight 分开保存
        self._primary = None
        self._applied_highlight = None
        # 最近一次写入后的完整调色板签名，用于识别外部重放
        self._applied_signature = None
        self._syncing_palette = False
        # 调色板变化后稍等一下再重载，避开菜单 / 对话框正在关闭的时机
        self._refresh_timer = QTimer()
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(120)
        self._refresh_timer.timeout.connect(self._resync_if_source_changed)

    def setup(self):
        pass

    def start(self):
        self._install_menu_filter()
        self._install_menu_animator()

        # 启动时只注入一次全局 QSS（很快，避免拖慢启动）
        self.apply_global_theme()

        # matugen 可能在运行中重新注入调色板，重新对齐选中态。
        # 必须在装 watcher 之前连好：watcher 可能在启动时就纠正一次
        # 「文件比进程新」的调色板。
        if self.app is not None:
            self.app.paletteChanged.connect(self._on_app_palette_changed)

        self._install_theme_watcher()

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

    def _install_theme_watcher(self):
        """监听 .colors 变化，换壁纸后不再需要重启 Krita。"""
        if self.theme_watcher is not None or self.app is None:
            return
        self.theme_watcher = ThemeWatcher(self.app)

    # ---- 主题 ----------------------------------------------------------

    def theme_colors(self):
        """当前调色板对应的语义色：QSS 与窗口补丁共用同一份。

        ``Highlight`` 会被插件改写为 ``primary-container``，所以主色必须
        来自单独的缓存。只有当调色板被 matugen / Krita 重新注入时
        （``Highlight`` 不再等于我们上次写入的值），才更新缓存。
        """
        if self.app is None:
            return None

        palette = self.app.palette()
        raw_highlight = QColor(palette.color(COLOR_ROLE.Highlight))
        if self._applied_highlight is None or raw_highlight != self._applied_highlight:
            self._primary = raw_highlight

        return get_theme_colors(palette, COLOR_ROLE, primary=self._primary)

    def _palette_signature(self, palette=None):
        """当前调色板的完整签名。

        必须包含 ``Highlight`` / ``HighlightedText``：Krita 用同一个
        ``.colors`` 重放主题时，``Window`` / ``WindowText`` / 主色都不会变，
        只有这两个角色被写回 matugen 原值。旧签名漏掉它们，导致重放被
        误判成「没有变化」而跳过修复。
        """
        palette = palette or self.app.palette()
        return (
            palette.color(COLOR_ROLE.Window).name(),
            palette.color(COLOR_ROLE.WindowText).name(),
            palette.color(COLOR_ROLE.Highlight).name(),
            palette.color(COLOR_ROLE.HighlightedText).name(),
        )

    def apply_global_theme(self):
        """只调一次 setStyleSheet，瞬间生效。"""
        colors = self.theme_colors()
        if colors is None:
            return

        # 先装好自绘指示器，再上 QSS：QSS 一变就会触发全局 repolish
        ensure_indicator_style(colors, self.app)
        qss = build_qss(colors, prepare_icons(colors))

        # 只有样式表真的变了才写入。
        # Krita 在配置对话框点「确定」后会用同一个 .colors 重放调色板，
        # 触发 refresh_theme；而 Qt 的 QApplication::setStyleSheet()
        # 会无条件对 styleRulesCache 里的所有控件做一次 repolish，
        # 此时对话框控件刚销毁、菜单刚重建，缓存里可能留下悬空指针，
        # 导致段错误。内容相同就跳过，既避免崩溃也少一次全量 repolish。
        if self.app.styleSheet() != qss:
            # 直接在已有样式表上 setStyleSheet 会走 QStyleSheetStyle::repolish(qApp)，
            # 遍历全局 styleRulesCache。切换 Krita 主题时缓存里可能有正在销毁
            # 的菜单 / 对话框控件，会在 Qt 内部踩到悬空指针直接段错误。
            # 先清空再设置，走 setStyle 的重建路径，避开全局 repolish。
            self.app.setStyleSheet("")
            ensure_indicator_style(colors, self.app)
            self.app.setStyleSheet(qss)

        self.sync_palette(colors)

    def sync_palette(self, colors):
        """把选中态同步到 QPalette。

        QSS 只负责画选中背景，文字颜色由 Qt / KDE 的 delegate 自己从
        调色板读取（例如 KPageListViewDelegate）。所以 ``Highlight`` /
        ``HighlightedText`` 必须与 QSS 的 ``primary-container`` 配色一致，
        否则会出现深色文字压在深色背景上。

        两参数版 ``setColor`` 会同时写入 Active / Inactive / Disabled 三组，
        窗口失焦时也不会退回成另一套颜色。
        """
        pal = self.app.palette()
        changed = False

        desired = (
            (COLOR_ROLE.Highlight, colors["PRIMARY_CONTAINER"]),
            (COLOR_ROLE.HighlightedText, colors["ON_PRIMARY_CONTAINER"]),
        )
        groups = (
            COLOR_GROUP.Active,
            COLOR_GROUP.Inactive,
            COLOR_GROUP.Disabled,
        )
        for role, value in desired:
            color = QColor(value)
            if any(pal.color(group, role) != color for group in groups):
                pal.setColor(role, color)  # 两参数版：一次写入三组
                changed = True

        # 记录我们写入的 Highlight，供 theme_colors() 区分是否被外部重置
        self._applied_highlight = QColor(colors["PRIMARY_CONTAINER"])

        disabled = (COLOR_ROLE.WindowText, COLOR_ROLE.Text, COLOR_ROLE.ButtonText)
        for role in disabled:
            color = QColor(colors["TEXT_DISABLED"])
            if pal.color(COLOR_GROUP.Disabled, role) != color:
                pal.setColor(COLOR_GROUP.Disabled, role, color)
                changed = True

        # 只在真正漂移时 setPalette，避免每次窗口创建都触发全局 repolish
        if changed:
            self._syncing_palette = True
            try:
                self.app.setPalette(pal)
            finally:
                self._syncing_palette = False

        # 写入完成后再记录签名，且包含选中态两个角色
        self._applied_signature = self._palette_signature()

    def _on_app_palette_changed(self, _palette):
        """外部（matugen / Krita）重新注入调色板后，异步对齐一次。"""
        if not self._syncing_palette:
            self._refresh_timer.start()

    def _resync_if_source_changed(self):
        """调色板任何一项被外部改写就重载；自己写入的值不会触发。"""
        if self.app is None:
            return

        # 切换主题时菜单还在关闭、对话框可能正在销毁，等它们处理完再重载，
        # 避免在全量 polish 时碰到半销毁的控件。
        if self.app.activePopupWidget() is not None or self.app.activeModalWidget() is not None:
            self._refresh_timer.start()
            return

        if self._palette_signature() != self._applied_signature:
            self.refresh_theme()

    def refresh_theme(self):
        """重载主题：QSS、调色板、已打开窗口的补丁一次刷新。"""
        self.apply_global_theme()
        self.apply_heavy_hacks()

    def apply_heavy_hacks(self, *_):
        """窗口级操作：带防重复检查，可被定时器和信号重复调用。"""
        colors = self.theme_colors()
        if colors is None:
            return

        # 跟随 DMS 的动效设置（reduceMotion / 时长 / 曲线）
        if self.menu_animator is not None:
            self.menu_animator.refresh_motion()

        # Krita 可能在插件启动之后才套用自己的调色板，这里补一次，
        # 保证选中态文字色不会退回 matugen 的原始 HighlightedText。
        self.sync_palette(colors)

        # 样式菜单会换掉代理样式，顺便确认勾选控件仍由我们自绘
        ensure_indicator_style(colors, self.app)

        for win in Krita.instance().windows():
            qwin = win.qwindow()
            patch_welcome_page(qwin, colors)
            patch_angle_spinbox(qwin)
            patch_layer_editor(qwin, colors)
            apply_menu_text_settings(qwin)
            apply_menu_visibility_settings(qwin)

        # 主题热切换时，已打开的配置对话框也要同步（关掉再开也能命中 Show 钩子）
        for widget in self.app.topLevelWidgets():
            if widget.isVisible():
                inherit_app_palette(widget, self.app)

    def createActions(self, window):
        # 只在这里挂载 DMS UI 菜单，不触发全局重绘
        setup_ui_settings(window, self)


instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()
