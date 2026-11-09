import re
from krita import Krita
try:
    from PyQt6.QtWidgets import QWidget, QListWidget, QMenu, QLabel
    from PyQt6.QtCore import QObject, QEvent, Qt
except ImportError:
    from PyQt5.QtWidgets import QWidget, QListWidget, QMenu, QLabel
    from PyQt5.QtCore import QObject, QEvent, Qt

def patch_welcome_page(qwin, colors):
    """修复 Krita 欢迎页 C++ 写死的样式"""
    new_file_btn = qwin.findChild(QWidget, "newFileLink")
    open_file_btn = qwin.findChild(QWidget, "openFileLink")
    recent_list = qwin.findChild(QListWidget, "recentDocumentsListView")
    
    # 1. 新建/打开按钮样式
    if new_file_btn or open_file_btn:
        btn_qss = f"""
            QWidget {{ 
                background-color: {colors['ITEM_BG']}; 
                border-radius: 6px; 
                color: {colors['TEXT']} !important; 
                padding: 8px 12px;
            }}
            QWidget:hover {{ background-color: {colors['HOVER_BG']}; }}
            QWidget:pressed {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']} !important; }}
        """
        for btn in [new_file_btn, open_file_btn]:
            if btn:
                btn.setStyleSheet(btn_qss)
                # 深度清理内部的 QLabel
                for lbl in btn.findChildren(QLabel):
                    text = lbl.text()
                    if not text: continue
                    # 如果这个标签本身就只有快捷键，直接隐藏
                    if "Ctrl" in text or "Alt" in text:
                        lbl.hide()
                        lbl.setFixedWidth(0)
                        continue
                    # 否则正常去掉括号里的快捷键
                    clean_text = re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', text).strip()
                    if text != clean_text:
                        lbl.setText(clean_text)
                    # 强制去掉下划线
                    lbl.setStyleSheet(f"text-decoration: none !important; color: {colors['TEXT']} !important; background: transparent;")

    # 2. 最近图像列表
    if recent_list:
        recent_list.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; }}
            QListWidget::item {{ color: {colors['TEXT']} !important; border-radius: 6px; padding: 2px; }}
            QListWidget::item:hover {{ background-color: {colors['HOVER_BG']}; }}
            QListWidget::item:selected {{ background-color: {colors['SELECT_BG']}; color: {colors['HIGHLIGHT_TEXT']} !important; }}
        """)

    # 3. 社区资源模块化（保留图标，去除下划线，悬停发亮）
    keywords = ["使用手册", "捐款支持", "KDE 社区", "源代码库", "新手入门", "用户社区", "官方网站"]
    for widget in qwin.findChildren(QWidget):
        try:
            if not widget.isVisible(): continue
                
            text = ""
            if hasattr(widget, "text") and callable(widget.text):
                text = widget.text()
                
            if text and any(kw in text for kw in keywords):
                # 【关键修改】仅去除 <a> 标签（去下划线），保留 <img> 标签（保留图标）
                clean_text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text, flags=re.DOTALL)
                # 去除 <style> 标签防乱码
                clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)
                
                if hasattr(widget, "setText") and widget.text() != clean_text:
                    widget.setText(clean_text)
                
                # 开启悬停追踪
                try:
                    widget.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
                except AttributeError:
                    widget.setAttribute(Qt.WA_Hover, True)
                    
                # 给这个控件套上统一圆角框
                widget.setStyleSheet(f"""
                    QLabel {{
                        background-color: {colors['ITEM_BG']};
                        border-radius: 6px;
                        padding: 6px 12px;
                        margin: 2px 0px;
                        color: {colors['TEXT']} !important;
                    }}
                    QLabel:hover {{
                        background-color: {colors['HOVER_BG']};
                    }}
                """)
        except Exception:
            pass


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