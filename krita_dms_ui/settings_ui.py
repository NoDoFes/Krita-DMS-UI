import re
from krita import Krita
try:
    from PyQt6.QtWidgets import QMenu
except ImportError:
    from PyQt5.QtWidgets import QMenu

def toggle_top_menu(qwin, menu_name, visible):
    """控制顶部菜单项的显示与隐藏"""
    menubar = qwin.menuBar()
    for action in menubar.actions():
        raw_text = action.text().replace("&", "")
        clean_text = re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', raw_text).strip()
        
        if clean_text == menu_name:
            action.setVisible(visible)
            break

def apply_menu_visibility_settings(qwin):
    """强制同步菜单显隐状态，防止被 Krita 内部重置"""
    menus = ["文件", "编辑", "视图", "图像", "图层", "选择", "滤镜", "工具", "设置", "窗口", "帮助"]
    for m_name in menus:
        is_visible = Krita.instance().readSetting("DMS_UI", f"show_{m_name}", "true") == "true"
        toggle_top_menu(qwin, m_name, is_visible)

def apply_menu_text_settings(qwin):
    """应用菜单文本设置（是否隐藏快捷键提示）"""
    hide = Krita.instance().readSetting("DMS_UI", "hide_menu_shortcuts", "true") == "true"
    menubar = qwin.menuBar()
    
    for action in menubar.actions():
        text = action.text()
        if not text or "DMS UI" in text:
            continue
            
        if hide:
            if not action.property("dms_original_text"):
                action.setProperty("dms_original_text", text)
            
            orig = action.property("dms_original_text")
            clean = orig.replace("&", "")
            clean = re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', clean).strip()
            
            if action.text() != clean:
                action.setText(clean)
        else:
            if action.property("dms_original_text"):
                orig = action.property("dms_original_text")
                if action.text() != orig:
                    action.setText(orig)

def setup_ui_settings(window, extension):
    """在菜单栏最右侧创建 DMS UI 菜单"""
    qwin = window.qwindow()
    menubar = qwin.menuBar()
    
    if getattr(extension, "_dms_menu", None) and extension._dms_menu.menuAction() in menubar.actions():
        return

    extension._dms_menu = menubar.addMenu("DMS UI")
    
    title_action = window.createAction("dms_menu_title", "--- 显示/隐藏顶部菜单 ---", "")
    title_action.setEnabled(False)
    extension._dms_menu.addAction(title_action)
    
    menus = ["文件", "编辑", "视图", "图像", "图层", "选择", "滤镜", "工具", "设置", "窗口", "帮助"]
    
    for m_name in menus:
        action = window.createAction(f"dms_toggle_{m_name}", m_name, "")
        action.setCheckable(True)
        
        is_visible = Krita.instance().readSetting("DMS_UI", f"show_{m_name}", "true") == "true"
        action.setChecked(is_visible)
        
        action.toggled.connect(lambda checked, name=m_name, q=qwin: on_menu_toggled(q, name, checked))
        extension._dms_menu.addAction(action)

    extension._dms_menu.addSeparator()
    action_hide_shortcuts = window.createAction("dms_hide_menu_shortcuts", "隐藏菜单栏快捷键提示", "")
    action_hide_shortcuts.setCheckable(True)
    
    is_hidden = Krita.instance().readSetting("DMS_UI", "hide_menu_shortcuts", "true") == "true"
    action_hide_shortcuts.setChecked(is_hidden)
    
    def on_shortcuts_toggled(checked, q=qwin):
        Krita.instance().writeSetting("DMS_UI", "hide_menu_shortcuts", str(checked).lower())
        apply_menu_text_settings(q)
        
    action_hide_shortcuts.toggled.connect(on_shortcuts_toggled)
    extension._dms_menu.addAction(action_hide_shortcuts)
    
    # 初次加载时应用一次
    apply_menu_text_settings(qwin)
    apply_menu_visibility_settings(qwin)

def on_menu_toggled(qwin, menu_name, checked):
    toggle_top_menu(qwin, menu_name, checked)
    Krita.instance().writeSetting("DMS_UI", f"show_{menu_name}", str(checked).lower())