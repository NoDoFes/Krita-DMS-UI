from krita import Krita
try:
    from PyQt6.QtWidgets import QMenu
except ImportError:
    from PyQt5.QtWidgets import QMenu

def toggle_top_menu(qwin, menu_name, visible):
    """控制顶部菜单项的显示与隐藏"""
    menubar = qwin.menuBar()
    for action in menubar.actions():
        # 提取纯净文本，例如把 "文件(&F)" 或者 "文件(F)" 提取为 "文件"
        raw_text = action.text().replace("&", "")
        clean_text = raw_text.split("(")[0].strip()
        
        if clean_text == menu_name:
            action.setVisible(visible)
            break

def setup_ui_settings(window, extension):
    """在菜单栏最右侧创建 DMS UI 菜单"""
    qwin = window.qwindow()
    menubar = qwin.menuBar()
    
    # 防止重复添加
    if getattr(extension, "_dms_menu", None) and extension._dms_menu.menuAction() in menubar.actions():
        return

    # 在菜单栏末尾创建新菜单
    extension._dms_menu = menubar.addMenu("DMS UI")
    
    # 添加一个不可点击的提示文字作为分组标题
    title_action = window.createAction("dms_menu_title", "--- 显示/隐藏顶部菜单 ---", "")
    title_action.setEnabled(False)
    extension._dms_menu.addAction(title_action)
    
    # 需要控制显示/隐藏的菜单列表
    menus = ["文件", "编辑", "视图", "图像", "图层", "选择", "滤镜", "工具", "设置", "窗口", "帮助"]
    
    for m_name in menus:
        action = window.createAction(f"dms_toggle_{m_name}", m_name, "")
        action.setCheckable(True)
        
        # 从配置文件读取状态，默认显示 (true)
        is_visible = Krita.instance().readSetting("DMS_UI", f"show_{m_name}", "true") == "true"
        action.setChecked(is_visible)
        
        # 使用闭包捕获当前的 m_name 和 qwin
        action.toggled.connect(lambda checked, name=m_name, q=qwin: on_menu_toggled(q, name, checked))
        extension._dms_menu.addAction(action)
        
        # 立即应用一次状态
        toggle_top_menu(qwin, m_name, is_visible)

    # 在这里可以继续添加其他分组，比如界面元素的开关（参考你的截图）
    extension._dms_menu.addSeparator()
    placeholder = window.createAction("dms_placeholder", "更多 UI 选项即将到来...", "")
    placeholder.setEnabled(False)
    extension._dms_menu.addAction(placeholder)

def on_menu_toggled(qwin, menu_name, checked):
    """当用户勾选/取消时触发"""
    toggle_top_menu(qwin, menu_name, checked)
    # 保存到 Krita 配置中
    Krita.instance().writeSetting("DMS_UI", f"show_{menu_name}", str(checked).lower())