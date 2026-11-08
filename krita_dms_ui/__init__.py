from krita import Krita, Extension

try:
    from PyQt6.QtWidgets import QApplication, QMenu
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QPalette, QColor
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMenu
    from PyQt5.QtCore import QTimer, Qt
    from PyQt5.QtGui import QPalette, QColor

MODERN_QSS = """
/* ================== DMS 动态高对比度实色版 ================== */

QMenuBar { background-color: palette(window); border: none; padding: 2px; }
QMenuBar::item { background: transparent; padding: 6px 16px; border-radius: 6px; margin: 0px 2px; color: {{TEXT}} !important; }
QMenuBar::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QMenuBar::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }

QMainWindow::separator { background-color: palette(window); width: 0px; height: 0px; }
QSplitter::handle { background-color: palette(window); }

QMenu { background-color: palette(base); border: 1px solid {{BORDER}}; border-radius: 8px; padding: 6px; }
QMenu::item { background-color: transparent; padding: 6px 24px 6px 12px; border-radius: 6px; color: {{TEXT}} !important; }
QMenu::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QMenu::item:disabled { color: {{TEXT_DISABLED}} !important; background-color: transparent !important; }

QDockWidget { border: none; margin: 4px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 6px; margin-top: 4px; }

QTabBar { background: transparent; border: none; }
QTabBar::tab { background: transparent; border: none; padding: 6px 16px; margin-right: 4px; border-radius: 6px; color: {{TEXT}} !important; }
QTabBar::tab:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QTabBar::tab:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QTabWidget::pane { border: none; border-top: 0px; background: palette(window); top: -2px; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

QTreeView, QListView, QListWidget { background-color: palette(window); border: none; outline: none; show-decoration-selected: 1; }
QTreeView::item, QListView::item, QListWidget::item { border-radius: 6px; padding: 4px; margin: 2px 0px; color: {{TEXT}} !important; }
QTreeView::item:hover:!selected, QListView::item:hover:!selected, QListWidget::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected { background-color: {{SELECT_BG}} !important; color: {{HIGHLIGHT_TEXT}} !important; }

QPushButton { background-color: palette(button); border: none; border-radius: 6px; padding: 5px 12px; color: {{TEXT}} !important; }
QPushButton:hover { background-color: {{HOVER_BG}}; }
QPushButton:pressed { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QPushButton:disabled { color: {{TEXT_DISABLED}} !important; background-color: palette(window) !important; }

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color: palette(base); border: none; border-radius: 6px; padding: 4px 8px; color: {{TEXT}} !important; }
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover { background-color: {{HOVER_BG}}; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }

QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background-color: palette(base); border: 1px solid {{BORDER}}; border-radius: 6px; selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}} !important; color: {{TEXT}} !important; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: palette(mid); min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: palette(highlight); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; border: none; height: 0px; }
"""

class DMSModernUIExtension(Extension):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()

    def setup(self):
        pass

    def createActions(self, window):
        pass

    def start(self):
        QTimer.singleShot(1000, self.apply_theme)
        notifier = Krita.instance().notifier()
        notifier.windowCreated.connect(self.reapply_theme)

    def reapply_theme(self):
        QTimer.singleShot(200, self.apply_theme)
        QTimer.singleShot(800, self.apply_theme)
        QTimer.singleShot(1500, self.apply_theme)

    def apply_theme(self):
        if not self.app:
            return
        
        pal = self.app.palette()
        try:
            bg_color = pal.color(QPalette.ColorRole.Window)
            matugen_highlight = pal.color(QPalette.ColorRole.Highlight)
        except AttributeError:
            bg_color = pal.color(QPalette.Window)
            matugen_highlight = pal.color(QPalette.Highlight)
            
        is_light = bg_color.lightness() >= 128
        
        # 提取 Matugen 高亮色的色相 (H) 和饱和度 (S)
        h, s, l, a = matugen_highlight.getHsl()
        
        if not is_light:
            # 深色模式
            text_color = "#cccccc"
            text_disabled = "#666666"
            hover_bg = "#2e2e2e"    # 悬停依然用纯净深灰
            
            # 【核心魔法】用 Matugen 的主题色相，但强行压暗明度，作为实色背景
            # 这样既保留了主题的“色彩倾向”，又不会像浅蓝色那样瞎眼
            select_color = QColor.fromHsl(h, int(s * 0.6), 80) # 明度压到 80/255
            select_bg = select_color.name()
            highlight_text = "#ffffff"  # 配纯白文字
            
            border_color = "rgba(255, 255, 255, 15)"
        else:
            # 浅色模式
            text_color = "#333333"
            text_disabled = "#aaaaaa"
            hover_bg = "#ebebeb"
            
            # 浅色模式下，用主题色相，强行提亮明度作为背景
            select_color = QColor.fromHsl(h, int(s * 0.4), 220) # 明度提到 220/255
            select_bg = select_color.name()
            highlight_text = "#000000"  # 配纯黑文字
            
            border_color = "rgba(0, 0, 0, 20)"

        # 1. 注入全局 QSS
        final_qss = MODERN_QSS.replace("{{TEXT}}", text_color)\
                              .replace("{{TEXT_DISABLED}}", text_disabled)\
                              .replace("{{HOVER_BG}}", hover_bg)\
                              .replace("{{SELECT_BG}}", select_bg)\
                              .replace("{{BORDER}}", border_color)\
                              .replace("{{HIGHLIGHT_TEXT}}", highlight_text)
        self.app.setStyleSheet(final_qss)

        # 2. 强行接管底层 QPalette，让图层面板等 C++ 控件与我们同步
        try:
            # 背景使用我们计算出的动态主题压暗色
            pal.setColor(QPalette.ColorRole.Highlight, QColor(select_bg))
            # 文字使用纯白或纯黑，保证绝对可读性
            pal.setColor(QPalette.ColorRole.HighlightedText, QColor(highlight_text))
            
            pal.setColor(QPalette.ColorRole.WindowText, QColor(text_color))
            pal.setColor(QPalette.ColorRole.Text, QColor(text_color))
            pal.setColor(QPalette.ColorRole.ButtonText, QColor(text_color))
            
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(text_disabled))
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(text_disabled))
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(text_disabled))
        except AttributeError:
            pal.setColor(QPalette.Highlight, QColor(select_bg))
            pal.setColor(QPalette.HighlightedText, QColor(highlight_text))
            pal.setColor(QPalette.WindowText, QColor(text_color))
            pal.setColor(QPalette.Text, QColor(text_color))
            pal.setColor(QPalette.ButtonText, QColor(text_color))
            pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(text_disabled))
            pal.setColor(QPalette.Disabled, QPalette.Text, QColor(text_disabled))
            pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(text_disabled))
            
        self.app.setPalette(pal)

        # 3. 清理菜单黑边
        for widget in self.app.allWidgets():
            if isinstance(widget, QMenu):
                self.fix_menu(widget)

    def fix_menu(self, menu):
        if menu.property("dms_polished"):
            return
        menu.setProperty("dms_polished", True)
        
        try:
            menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        except AttributeError:
            menu.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WA_TranslucentBackground, True)

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()