import re
from krita import Krita
try:
    from PyQt6.QtWidgets import QWidget, QListWidget, QMenu, QLabel, QCheckBox, QRadioButton, QApplication
    from PyQt6.QtCore import QObject, QEvent, Qt
    from PyQt6.QtGui import QPalette
    COLOR_ROLE = QPalette.ColorRole
except ImportError:
    from PyQt5.QtWidgets import QWidget, QListWidget, QMenu, QLabel, QCheckBox, QRadioButton, QApplication
    from PyQt5.QtCore import QObject, QEvent, Qt
    from PyQt5.QtGui import QPalette
    COLOR_ROLE = QPalette

def patch_welcome_page(qwin, colors):
    """修复 Krita 欢迎页 C++ 写死的样式"""
    if qwin.property("dms_welcome_color") == colors['ITEM_BG']:
        return
    qwin.setProperty("dms_welcome_color", colors['ITEM_BG'])

    new_file_btn = qwin.findChild(QWidget, "newFileLink")
    open_file_btn = qwin.findChild(QWidget, "openFileLink")
    recent_list = qwin.findChild(QListWidget, "recentDocumentsListView")
    
    if new_file_btn or open_file_btn:
        btn_qss = f"""
            QWidget {{ 
                background-color: {colors['ITEM_BG']}; 
                border-radius: 6px; 
                color: {colors['TEXT']}; 
                padding: 8px 12px;
            }}
            QWidget:hover {{ background-color: {colors['HOVER_BG']}; }}
            QWidget:pressed {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']}; }}
        """
        for btn in [new_file_btn, open_file_btn]:
            if btn:
                btn.setStyleSheet(btn_qss)
                for lbl in btn.findChildren(QLabel):
                    text = lbl.text()
                    if not text: continue
                    if "Ctrl" in text or "Alt" in text:
                        lbl.hide()
                        lbl.setFixedWidth(0)
                        continue
                    clean_text = re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', text).strip()
                    if text != clean_text:
                        lbl.setText(clean_text)
                    lbl.setStyleSheet(f"text-decoration: none; color: {colors['TEXT']}; background: transparent;")

    if recent_list:
        recent_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{ color: {colors['TEXT']}; border-radius: 6px; padding: 2px; }}
            QListWidget::item:hover {{ background-color: {colors['HOVER_BG']}; }}
            QListWidget::item:selected {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']}; }}
        """)

    keywords = ["使用手册", "捐款支持", "KDE 社区", "源代码库", "新手入门", "用户社区", "官方网站"]
    for widget in qwin.findChildren(QWidget):
        try:
            if not widget.isVisible(): continue
            text = ""
            if hasattr(widget, "text") and callable(widget.text):
                text = widget.text()
                
            if text and any(kw in text for kw in keywords):
                if widget.property("dms_link_styled"):
                    continue
                widget.setProperty("dms_link_styled", True)
                
                clean_text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text, flags=re.DOTALL)
                clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)
                
                if hasattr(widget, "setText") and widget.text() != clean_text:
                    widget.setText(clean_text)
                
                try:
                    widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
                except AttributeError:
                    widget.setAttribute(Qt.WA_Hover, True)
                    
                widget.setStyleSheet(f"""
                    QLabel {{
                        background-color: {colors['ITEM_BG']};
                        border-radius: 6px;
                        padding: 6px 12px;
                        margin: 2px 0px;
                        color: {colors['TEXT']};
                    }}
                    QLabel:hover {{
                        background-color: {colors['HOVER_BG']};
                    }}
                """)
                
                parent = widget.parentWidget()
                while parent and parent != qwin:
                    # 【核心修复】限制最大宽度和高度，防止涂色到整个左侧大容器
                    if 100 < parent.width() < 350 and 25 < parent.height() < 60:
                        try:
                            parent.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                        except AttributeError:
                            parent.setAttribute(Qt.WA_StyledBackground, True)
                            
                        parent.setStyleSheet(f"""
                            QWidget {{
                                background-color: {colors['ITEM_BG']};
                                border-radius: 6px;
                                padding: 4px 8px;
                                margin: 2px 0px;
                            }}
                            QWidget:hover {{
                                background-color: {colors['HOVER_BG']};
                            }}
                            QLabel {{
                                background: transparent;
                                color: {colors['TEXT']};
                                text-decoration: none;
                            }}
                        """)
                        break
                    parent = parent.parentWidget()
        except Exception:
            pass

class MenuFilter(QObject):
    """全局事件过滤器：去黑边 + 修复内嵌菜单文字消失"""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Polish:
            if isinstance(obj, QMenu):
                # 1. 去黑边
                if not obj.property("dms_polished"):
                    obj.setProperty("dms_polished", True)
                    try:
                        obj.setWindowFlags(obj.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                        obj.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                    except AttributeError:
                        obj.setWindowFlags(obj.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                        obj.setAttribute(Qt.WA_TranslucentBackground, True)
                
                # 2. 修复内嵌菜单文字消失
                app = QApplication.instance()
                if app:
                    text_color = app.palette().color(COLOR_ROLE.WindowText).name()
                    for action in obj.actions():
                        if hasattr(action, "defaultWidget") and action.defaultWidget():
                            w = action.defaultWidget()
                            for child in w.findChildren(QWidget):
                                if isinstance(child, (QLabel, QCheckBox, QRadioButton)):
                                    child.setStyleSheet(f"color: {text_color}; background: transparent;")
        return False