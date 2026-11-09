import re
from krita import Krita
try:
    from PyQt6.QtWidgets import QMenu
except ImportError:
    from PyQt5.QtWidgets import QMenu

# 内部中文名 -> 英文名（Krita 英文界面下回退匹配用）
_MENU_EN = {
    "文件": "File", "编辑": "Edit", "视图": "View", "图像": "Image",
    "图层": "Layer", "选择": "Select", "滤镜": "Filter", "工具": "Tools",
    "设置": "Settings", "窗口": "Window", "帮助": "Help",
}

def _clean_menu_text(text):
    """去掉 & 与末尾 (快捷键) 提示"""
    raw = text.replace("&", "")
    return re.sub(r'\s*[\(（][^\)）]*[\)）]$', '', raw).strip()

def _matches_menu(action_text, menu_name):
    """中文名优先，英文名回退，兼容 Krita 英文界面"""
    clean = _clean_menu_text(action_text)
    return clean == menu_name or clean == _MENU_EN.get(menu_name, "")

def toggle_top_menu(qwin, menu_name, visible):
    """控制顶部菜单项的显示与隐藏"""
    menubar = qwin.menuBar()
    for action in menubar.actions():
        if _matches_menu(action.text(), menu_name):
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
            clean = _clean_menu_text(orig)
            
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
    
    extension._dms_menu.addSeparator()
    action_refresh = window.createAction("dms_refresh_theme", "🔄 重载当前主题色", "")
    action_refresh.triggered.connect(extension.apply_global_theme) 
    extension._dms_menu.addAction(action_refresh)
    
    # 初次加载时应用一次
    apply_menu_text_settings(qwin)
    apply_menu_visibility_settings(qwin)

def on_menu_toggled(qwin, menu_name, checked):
    """当用户勾选/取消时触发"""
    toggle_top_menu(qwin, menu_name, checked)
    Krita.instance().writeSetting("DMS_UI", f"show_{menu_name}", str(checked).lower())