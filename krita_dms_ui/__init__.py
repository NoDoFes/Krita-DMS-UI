from krita import Krita, Extension

# 兼容 PyQt5 和 PyQt6
try:
    from PyQt6.QtWidgets import QApplication, QMenu
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QPalette, QColor
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMenu
    from PyQt5.QtCore import QTimer, Qt
    from PyQt5.QtGui import QPalette, QColor

# 将动态变化的颜色写成占位符 {{...}}
MODERN_QSS = """
/* ================== DMS 全自动明暗适配 ================== */

/* 1. 顶部菜单栏 */
QMenuBar {
    background-color: palette(window);
    border: none;
    padding: 2px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 16px;
    border-radius: 6px;
    margin: 0px 2px;
    color: {{TEXT}} !important;
}
QMenuBar::item:hover:!selected {
    background-color: {{HOVER_BG}};
    color: {{TEXT}} !important;
}
QMenuBar::item:selected {
    background-color: {{SELECT_BG}};
    color: {{HIGHLIGHT}} !important; 
}

/* 2. 消除白线与分割线 */
QMainWindow::separator { background-color: palette(window); width: 0px; height: 0px; }
QSplitter::handle { background-color: palette(window); }

/* 3. 右键菜单 / 下拉菜单 */
QMenu {
    background-color: palette(base);
    border: 1px solid {{BORDER}};
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    background-color: transparent;
    padding: 6px 24px 6px 12px;
    border-radius: 6px;
    color: {{TEXT}} !important;
}
QMenu::item:selected {
    background-color: {{SELECT_BG}}; 
    color: {{HIGHLIGHT}} !important; 
}
QMenu::item:disabled {
    color: {{TEXT_DISABLED}} !important;
    background-color: transparent !important;
}

/* 4. Docker 面板 */
QDockWidget { border: none; margin: 4px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 6px; margin-top: 4px; }

/* 5. Docker 内的标签页 */
QTabBar { background: transparent; border: none; }
QTabBar::tab {
    background: transparent;
    border: none;
    padding: 6px 16px;
    margin-right: 4px;
    border-radius: 6px;
    color: {{TEXT}} !important;
}
QTabBar::tab:hover:!selected { 
    background-color: {{HOVER_BG}}; 
    color: {{TEXT}} !important;
}
QTabBar::tab:selected { 
    background-color: {{SELECT_BG}};
    color: {{HIGHLIGHT}} !important;
}
QTabWidget::pane { border: none; border-top: 0px; background: palette(window); top: -2px; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

/* 6. 树状列表 / 设置面板 / 图层面板 */
QTreeView, QListView, QListWidget {
    background-color: palette(window);
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QTreeView::item, QListView::item, QListWidget::item {
    border-radius: 6px;
    padding: 4px;
    margin: 2px 0px;
    color: {{TEXT}} !important;
}
QTreeView::item:hover:!selected, 
QListView::item:hover:!selected, 
QListWidget::item:hover:!selected {
    background-color: {{HOVER_BG}}; 
    color: {{TEXT}} !important;
}
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected {
    background-color: {{SELECT_BG}} !important; 
    color: {{HIGHLIGHT}} !important; 
}

/* 7. 按钮、输入框、下拉框 */
QPushButton {
    background-color: palette(button);
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    color: {{TEXT}} !important;
}
QPushButton:hover { 
    background-color: {{HOVER_BG}}; 
}
QPushButton:pressed { 
    background-color: {{SELECT_BG}}; 
}
QPushButton:disabled {
    color: {{TEXT_DISABLED}} !important;
    background-color: palette(window) !important;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: palette(base);
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    color: {{TEXT}} !important;
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    background-color: {{HOVER_BG}}; 
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    background-color: {{SELECT_BG}}; 
}

QComboBox::drop-down { border: none; width: 20px; }

QComboBox QAbstractItemView {
    background-color: palette(base);
    border: 1px solid {{BORDER}};
    border-radius: 6px;
    selection-background-color: {{SELECT_BG}};
    selection-color: {{HIGHLIGHT}} !important;
    color: {{TEXT}} !important;
}

/* 8. 滚动条 */
QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: palette(mid); min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: palette(highlight); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none; border: none; height: 0px;
}
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

    def apply_theme(self):
        if not self.app:
            return
        
        print("DMS UI: 正在检测明暗模式并计算交互色彩...")
        
        pal = self.app.palette()
        
        # 1. 获取当前窗口背景色，判断是深色还是浅色模式
        try:
            bg_color = pal.color(QPalette.ColorRole.Window)
            highlight_color = pal.color(QPalette.ColorRole.Highlight)
        except AttributeError:
            bg_color = pal.color(QPalette.Window)
            highlight_color = pal.color(QPalette.Highlight)
            
        # 2. 核心：根据背景亮度决定色彩策略
        if bg_color.lightness() < 128:
            # ----- 深色模式 (Dark Mode) -----
            text_color = "#cccccc"
            text_disabled = "rgba(204, 204, 204, 80)"
            hover_bg = "rgba(255, 255, 255, 20)"  # 白光
            select_bg = "rgba(255, 255, 255, 40)"
            border_color = "rgba(255, 255, 255, 15)"
            
            # 深色模式下，主题高亮色如果太暗，就提亮
            if highlight_color.lightness() < 160:
                highlight_color = highlight_color.lighter(180)
                
        else:
            # ----- 浅色模式 (Light Mode) -----
            text_color = "#444444"  # 深灰
            text_disabled = "rgba(68, 68, 68, 80)"
            hover_bg = "rgba(0, 0, 0, 15)"  # 黑光
            select_bg = "rgba(0, 0, 0, 30)"
            border_color = "rgba(0, 0, 0, 20)"
            
            # 浅色模式下，主题高亮色如果太亮（比如亮黄/亮青），就加深
            if highlight_color.lightness() > 160:
                highlight_color = highlight_color.darker(150)

        safe_highlight = highlight_color.name()
        
        # 3. 将动态计算的颜色替换进 QSS
        final_qss = MODERN_QSS.replace("{{TEXT}}", text_color)\
                              .replace("{{TEXT_DISABLED}}", text_disabled)\
                              .replace("{{HOVER_BG}}", hover_bg)\
                              .replace("{{SELECT_BG}}", select_bg)\
                              .replace("{{BORDER}}", border_color)\
                              .replace("{{HIGHLIGHT}}", safe_highlight)
        
        self.app.setStyleSheet(final_qss)
        
        # 4. 清理菜单黑边
        for widget in self.app.allWidgets():
            if isinstance(widget, QMenu):
                self.fix_menu(widget)
                
        # 5. 同步底层调色板（给原生 C++ 控件兜底）
        try:
            pal.setColor(QPalette.ColorRole.WindowText, QColor(text_color))
            pal.setColor(QPalette.ColorRole.Text, QColor(text_color))
            pal.setColor(QPalette.ColorRole.ButtonText, QColor(text_color))
            pal.setColor(QPalette.ColorRole.HighlightedText, highlight_color)
            
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(text_disabled))
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(text_disabled))
            pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(text_disabled))
        except AttributeError:
            # PyQt5
            pal.setColor(QPalette.WindowText, QColor(text_color))
            pal.setColor(QPalette.Text, QColor(text_color))
            pal.setColor(QPalette.ButtonText, QColor(text_color))
            pal.setColor(QPalette.HighlightedText, highlight_color)
            
            pal.setColor(QPalette.Disabled, QPalette.WindowText, QColor(text_disabled))
            pal.setColor(QPalette.Disabled, QPalette.Text, QColor(text_disabled))
            pal.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(text_disabled))

        self.app.setPalette(pal)

    def fix_menu(self, menu):
        if menu.property("dms_polished"):
            return
        menu.setProperty("dms_polished", True)
        
        try:
            menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        except AttributeError:
            menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WA_TranslucentBackground, True)

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()