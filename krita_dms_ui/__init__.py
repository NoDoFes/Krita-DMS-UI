from krita import Krita, Extension
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QPalette, QColor
    COLOR_ROLE = QPalette.ColorRole
    COLOR_GROUP = QPalette.ColorGroup
except ImportError:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    from PyQt5.QtGui import QPalette, QColor
    COLOR_ROLE = QPalette
    COLOR_GROUP = QPalette

from .styles import get_theme_colors, build_qss
from .hacks import patch_welcome_page, MenuFilter
# 导入显隐控制
from .settings_ui import setup_ui_settings, apply_menu_text_settings, apply_menu_visibility_settings

class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.menu_filter = None
        self._dms_menu = None

    def setup(self): pass

    def start(self):
        if not self.menu_filter:
            self.menu_filter = MenuFilter(self.app)
            self.app.installEventFilter(self.menu_filter)

        # 启动时：只做一次全局 QSS 注入（极快，200ms以内）
        self.apply_global_theme()
        
        # 把处理欢迎页、菜单文本等脏活累活，延迟 1 秒放到后台做
        QTimer.singleShot(1000, self.apply_heavy_hacks)
        
        # 【核心修复】监听窗口创建，确保新开窗口时状态不丢失
        Krita.instance().notifier().windowCreated.connect(self.apply_heavy_hacks)

    def createActions(self, window):
        # 只在这里挂载 DMS UI 菜单，不触发全局重绘
        setup_ui_settings(window, self)

    def apply_global_theme(self):
        """核心：只调一次 setStyleSheet，瞬间生效"""
        if not self.app: return
        pal = self.app.palette()
        colors = get_theme_colors(pal, COLOR_ROLE)
        
        self.app.setStyleSheet(build_qss(colors))

        pal.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
        pal.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
        pal.setColor(COLOR_ROLE.WindowText, QColor(colors["TEXT"]))
        pal.setColor(COLOR_ROLE.Text, QColor(colors["TEXT"]))
        pal.setColor(COLOR_ROLE.ButtonText, QColor(colors["TEXT"]))
        
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.WindowText, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.Text, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.ButtonText, QColor(colors["TEXT_DISABLED"]))
        self.app.setPalette(pal)

    def apply_heavy_hacks(self):
        """耗时操作：放在后台，带防重复检查"""
        if not self.app: return
        pal = self.app.palette()
        colors = get_theme_colors(pal, COLOR_ROLE)

        for win in Krita.instance().windows():
            qwin = win.qwindow()
            # 1. 处理欢迎页
            patch_welcome_page(qwin, colors)
            
            # 2. 处理菜单文本
            apply_menu_text_settings(qwin)
            
            # 3. 【核心修复】强制把菜单显隐状态按回去！
            apply_menu_visibility_settings(qwin)

instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()