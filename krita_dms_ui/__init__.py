from krita import Krita, Extension
try:
    from PyQt6.QtWidgets import QApplication, QMenu
    from PyQt6.QtCore import QTimer, Qt
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMenu
    from PyQt5.QtCore import QTimer, Qt

# 极致精简版 QSS：绝对不碰主界面布局、不碰画布周边、不碰高频重绘的滚动条
MODERN_QSS = """
/* 仅针对菜单：圆角 + 动态颜色 */
QMenu {
    background-color: palette(window);
    border: 1px solid palette(mid);
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    background-color: transparent;
    color: palette(window-text);
    padding: 6px 24px 6px 12px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}
QMenu::separator {
    height: 1px;
    background: palette(mid);
    margin: 4px 8px;
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
        # 延迟 1 秒执行，等主窗口完全加载
        QTimer.singleShot(1000, self.apply_theme)

    def apply_theme(self):
        if not self.app:
            return
        print("DMS UI: 正在注入精简版 QSS...")
        
        # 1. 应用 QSS
        self.app.setStyleSheet(MODERN_QSS)
        
        # 2. 仅仅遍历一次现有的菜单，去掉黑边。
        # 绝不使用 installEventFilter，还你丝滑画笔！
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
            menu.setAttribute(Qt.WA_TranslucentBac | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WA_TranslucentBackground, True)

# 注册
instance = Krita.instance()
extension = DMSModernUIExtension(instance)
instance.addExtension(extension)
extension.start()