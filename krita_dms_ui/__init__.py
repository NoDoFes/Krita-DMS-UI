from krita import Krita, Extension

try:
    from PyQt6.QtWidgets import QApplication, QAbstractItemView
    from PyQt6.QtCore import QTimer
    from PyQt6.QtGui import QPalette, QColor
    COLOR_ROLE = QPalette.ColorRole
    COLOR_GROUP = QPalette.ColorGroup
except ImportError:
    from PyQt5.QtWidgets import QApplication, QAbstractItemView
    from PyQt5.QtCore import QTimer
    from PyQt5.QtGui import QPalette, QColor
    COLOR_ROLE = QPalette
    COLOR_GROUP = QPalette

from .styles import get_theme_colors, build_qss
from .hacks import patch_welcome_page, MenuFilter
from .settings_ui import setup_ui_settings

class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.last_highlight_color = None
        self.menu_filter = None
        self._dms_menu = None

    def setup(self): pass

    def start(self):
        if not self.menu_filter:
            self.menu_filter = MenuFilter(self.app)
            self.app.installEventFilter(self.menu_filter)

        self.apply_theme()
        
        notifier = Krita.instance().notifier()
        notifier.windowCreated.connect(self.apply_theme)
        
        self.theme_watcher = QTimer()
        self.theme_watcher.timeout.connect(self.check_theme_change)
        self.theme_watcher.start(2000)

    def createActions(self, window):
        self.apply_theme()
        # 在菜单栏创建独立 UI 选项
        setup_ui_settings(window, self)

    def check_theme_change(self):
        pal = self.app.palette()
        current_hl = pal.color(COLOR_ROLE.Highlight).name()
        if self.last_highlight_color != current_hl:
            self.apply_theme()

    def apply_theme(self):
        if not self.app: return
        
        pal = self.app.palette()
        self.last_highlight_color = pal.color(COLOR_ROLE.Highlight).name()
        
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

        for win in Krita.instance().windows():
            qwin = win.qwindow()
            patch_welcome_page(qwin, colors)
            
            for view in qwin.findChildren(QAbstractItemView):
                p = view.palette()
                p.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
                p.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                p.setColor(COLOR_GROUP.Active, COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                p.setColor(COLOR_GROUP.Inactive, COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                view.setPalette(p)
                if view.viewport():
                    view.viewport().setPalette(p)
                view.setStyleSheet(f"QAbstractItemView {{ selection-color: {colors['HIGHLIGHT_TEXT']} !important; }} QTreeView::item:selected {{ color: {colors['HIGHLIGHT_TEXT']} !important; }}")

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()