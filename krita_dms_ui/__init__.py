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

# 从我们分离的模块导入
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
        
        # 1. 计算颜色并应用 QSS
        colors = get_theme_colors(pal, COLOR_ROLE)
        self.app.setStyleSheet(build_qss(colors))

        # 2. 强制接管底层 QPalette
        try:
            pal.setColor(COLOR_ROLE.Highlight, QColor(colors["SELECT_BG"]))
            pal.setColor(COLOR_ROLE.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
            pal.setColor(COLOR_ROLE.WindowText, QColor(colors["TEXT"]))
            pal.setColor(COLOR_ROLE.Text, QColor(colors["TEXT"]))
            pal.setColor(COLOR_ROLE.ButtonText, QColor(colors["TEXT"]))
            
            pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.WindowText, QColor(colors["TEXT_DISABLED"]))
            pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.Text, QColor(colors["TEXT_DISABLED"]))
            pal.setColor(COLOR_GROUP.Disabled, COLOR_ROLE.ButtonText, QColor(colors["TEXT_DISABLED"]))
        except AttributeError:
            pal.setColor(QPalette.Highlight, QColor(colors["SELECT_BG"]))
            pal.setColor(QPalette.HighlightedText, QColor(colors["HIGHLIGHT_TEXT"]))
            pal.setColor(QPalette.WindowText, QColor(colors["TEXT"]))
            pal.setColor(QPalette.Text, QColor(colors["TEXT"]))
            pal.setColor(QPalette.ButtonText, QColor(colors["TEXT"]))
            pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(colors["TEXT_DISABLED"]))
            pal.setColor(QPalette.Disabled, QPalette.Text, QColor(colors["TEXT_DISABLED"]))
            pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors["TEXT_DISABLED"]))
        self.app.setPalette(pal)

        # 3. 执行底层 Hack（欢迎页 + 菜单）
        patch_welcome_page(colors)
        fix_menu_edges()

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()