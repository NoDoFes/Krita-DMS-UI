from krita import Krita
try:
    from PyQt6.QtWidgets import QWidget, QListWidget, QMenu
    from PyQt6.QtCore import QObject, QEvent, Qt
except ImportError:
    from PyQt5.QtWidgets import QWidget, QListWidget, QMenu
    from PyQt5.QtCore import QObject, QEvent, Qt

def patch_welcome_page(qwin, colors):
    """修复 Krita 欢迎页 C++ 写死的样式"""
    new_file_btn = qwin.findChild(QWidget, "newFileLink")
    open_file_btn = qwin.findChild(QWidget, "openFileLink")
    recent_list = qwin.findChild(QListWidget, "recentDocumentsListView")
    
    if new_file_btn or open_file_btn:
        btn_qss = f"""
            QWidget {{ background-color: transparent; border-radius: 6px; color: {colors['TEXT']} !important; }}
            QWidget:hover {{ background-color: {colors['HOVER_BG']}; }}
            QWidget:pressed {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']} !important; }}
        """
        if new_file_btn: new_file_btn.setStyleSheet(btn_qss)
        if open_file_btn: open_file_btn.setStyleSheet(btn_qss)
            
    if recent_list:
        recent_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{ color: {colors['TEXT']} !important; border-radius: 6px; padding: 2px; }}
            QListWidget::item:hover {{ background-color: {colors['HOVER_BG']}; }}
            QListWidget::item:selected {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']} !important; }}
        """)

class MenuFilter(QObject):
    """全局事件过滤器：在菜单弹出前的一瞬间，强行剥去原生边框，保证 QSS 圆角完美生效"""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish:
            if isinstance(obj, QMenu):
                if not obj.property("dms_polished"):
                    obj.setProperty("dms_polished", True)
                    try:
                        obj.setWindowFlags(obj.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                        obj.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                    except AttributeError:
                        obj.setWindowFlags(obj.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                        obj.setAttribute(Qt.WA_TranslucentBackground, True)
        return False