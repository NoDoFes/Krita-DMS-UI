from krita import Krita, Extension
try:
    from PyQt6.QtWidgets import QApplication, QMenu
    from PyQt6.QtCore import QTimer, Qt
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMenu
    from PyQt5.QtCore import QTimer, Qt

MODERN_QSS = """
/* ================== 统一交互反馈：白色微光叠加 ================== */

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
    color: palette(window-text);
}
/* 菜单栏的悬停/激活 */
QMenuBar::item:selected, QMenuBar::item:hover {
    background-color: rgba(255, 255, 255, 20);
    color: palette(window-text);
}

/* 2. 消除白线与分割线 */
QMainWindow::separator { background-color: palette(window); width: 0px; height: 0px; }
QSplitter::handle { background-color: palette(window); }

/* 3. 右键菜单 */
QMenu {
    background-color: palette(base);
    border: 1px solid rgba(255, 255, 255, 15);
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    background-color: transparent;
    color: palette(window-text);
    padding: 6px 24px 6px 12px;
    border-radius: 6px;
}
/* 下拉菜单的悬停 (通常保留高亮色，如果你希望菜单也微亮，可以改成 rgba(255, 255, 255, 20) ) */
QMenu::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}

/* 4. Docker 面板 */
QDockWidget { border: none; margin: 4px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 6px; margin-top: 4px; }

/* 5. Docker 内的标签页 (图层/工具选项/拾色器) */
QTabBar { background: transparent; border: none; }
QTabBar::tab {
    background: transparent;
    color: palette(window-text);
    border: none;
    padding: 6px 16px;
    margin-right: 4px;
    border-radius: 6px;
}
/* 选中的 Tab：给它稍微强一点的微光 (40)，或者保留当前的底色 */
QTabBar::tab:selected { 
    background-color: rgba(255, 255, 255, 30); /* 选中状态稍亮 */
    color: palette(highlight); 
}
/* 未选中的 Tab 悬停 */
QTabBar::tab:hover:!selected { 
    background-color: rgba(255, 255, 255, 20); 
}

QTabWidget::pane { border: none; border-top: 0px; background: palette(window); top: -2px; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

/* 6. 树状列表 (设置面板、图层面板) */
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
}
/* 列表项的悬停 */
QTreeView::item:hover:!selected, 
QListView::item:hover:!selected, 
QListWidget::item:hover:!selected {
    background-color: rgba(255, 255, 255, 20); 
}
/* 列表项的选中 */
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected {
    background-color: palette(highlight);
    color: #111111; 
    font-weight: bold;
}

/* ================== 7. 各种输入部件 (全面悬停响应) ================== */

/* 普通按钮 */
QPushButton {
    background-color: palette(button);
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    color: palette(button-text);
}
QPushButton:hover { 
    background-color: rgba(255, 255, 255, 20); 
}
QPushButton:pressed { 
    background-color: rgba(255, 255, 255, 40); 
}

/* 文本输入框、数字微调框、下拉框 (统一背景与悬停) */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: palette(base);
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
    color: palette(text);
}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    background-color: rgba(255, 255, 255, 20); /* 鼠标悬停时整体微亮 */
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    background-color: rgba(255, 255, 255, 30); /* 输入获取焦点时更亮一点 */
}

/* 针对下拉框的下拉菜单区域 */
QComboBox QAbstractItemView {
    background-color: palette(base);
    border: 1px solid rgba(255, 255, 255, 15);
    border-radius: 6px;
    selection-background-color: palette(highlight);
    selection-color: palette(highlighted-text);
}

/* 🔪 补杀 1：有些下拉框用的是 QListView，强制加上微光悬停 */
QComboBox QAbstractItemView::item {
    padding: 4px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: rgba(255, 255, 255, 20);
}

/* 🔪 补杀 2：Krita 很多复杂的下拉框（比如带分类的），其实是个 QTreeView */
QComboBox QTreeView {
    background-color: palette(base);
    border: 1px solid rgba(255, 255, 255, 15);
    border-radius: 6px;
    outline: none;
}
QComboBox QTreeView::item {
    padding: 4px;
    border-radius: 4px;
}
QComboBox QTreeView::item:hover {
    background-color: rgba(255, 255, 255, 20);
}
QComboBox QTreeView::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}

/* 复选框和单选框 */
QCheckBox, QRadioButton {
    background: transparent;
    spacing: 6px;
}
QCheckBox:hover, QRadioButton:hover {
    color: rgba(255, 255, 255, 255); /* 文字变白提亮 */
}

/* ================== 特别针对滑条的悬停 ================== */
QSlider::groove:horizontal {
    height: 6px;
    background: rgba(255, 255, 255, 30);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: palette(highlight);
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::handle:horizontal:hover {
    background: rgba(255, 255, 255, 200); /* 滑块悬停变白 */
}

/* 针对截图中那些粉红色的已填充轨道 (sub-page) */
QSlider::sub-page:horizontal {
    background: palette(highlight);
    border-radius: 3px;
}
/* 给已填充轨道加上悬停效果（虽然部分原生控件可能不吃这个，但写了总比没有好） */
QSlider:hover::sub-page:horizontal {
    background: rgba(255, 255, 255, 180);
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
        
        print("DMS UI: 注入 UI 样式（纯 QSS 回退版）...")
        self.app.setStyleSheet(MODERN_QSS)
        
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
            menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WA_TranslucentBackground, True)

# 注册插件
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()