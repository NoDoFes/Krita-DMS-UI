from krita import Krita
try:
    from PyQt6.QtWidgets import QWidget, QListWidget, QMenu
    from PyQt6.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import QWidget, QListWidget, QMenu
    from PyQt5.QtCore import Qt

def patch_welcome_page(colors):
    for win in Krita.instance().windows():
        qwin = win.qwindow()
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

def fix_menu_edges():
    for win in Krita.instance().windows():
        qwin = win.qwindow()
        for widget in qwin.findChildren(QMenu):
            if widget.property("dms_polished"):
                continue
            widget.setProperty("dms_polished", True)
            try:
                widget.setWindowFlags(widget.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            except AttributeError:
                widget.setWindowFlags(widget.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                widget.setAttribute(Qt.WA_TranslucentBackground, True)