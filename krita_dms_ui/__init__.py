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
from .hacks import patch_welcome_page, fix_menu_edges

class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()

    def setup(self): pass
    def createActions(self, window): pass

    def start(self):
        QTimer.singleShot(1000, self.apply_theme)
        notifier = Krita.instance().notifier()
        notifier.windowCreated.connect(self.reapply_theme)

    def reapply_theme(self):
        QTimer.singleShot(200, self.apply_theme)
        QTimer.singleShot(800, self.apply_theme)
        QTimer.singleShot(1500, self.apply_theme)

    def apply_theme(self):
        if not self.app: return
        
        pal = self.app.palette()
        
        colors = get_theme_colors(pal, COLOR_ROLE)
        self.app.setStyleSheet(build_qss(colors))

        # 强制接管全局 Palette
        pal.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
        pal.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
        pal.setColor(COLOR_ROLE.WindowText, QColor(colors["TEXT"]))
        pal.setColor(COLOR_ROLE.Text, QColor(colors["TEXT"]))
        pal.setColor(COLOR_ROLE.ButtonText, QColor(colors["TEXT"]))
        
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.WindowText, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.Text, QColor(colors["TEXT_DISABLED"]))
        pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.ButtonText, QColor(colors["TEXT_DISABLED"]))
        self.app.setPalette(pal)

        patch_welcome_page(colors)
        fix_menu_edges()

        # 针对图层、通道等 C++ 自绘列表，直接洗脑它们的内部调色板
        for win in Krita.instance().windows():
            for view in win.qwindow().findChildren(QAbstractItemView):
                p = view.palette()
                p.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
                p.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                p.setColor(COLOR_GROUP.Active, COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                p.setColor(COLOR_GROUP.Inactive, COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
                view.setPalette(p)
                if view.viewport():
                    view.viewport().setPalette(p)

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()