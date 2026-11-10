"""DMS UI 菜单与设置持久化。

设置键统一在这个文件里定义，避免字符串散落到各个模块。
"""

import re

from krita import Krita

from .qt_compat import QMenu

# ---- 设置键 ------------------------------------------------------------

SETTINGS_GROUP = "DMS_UI"
SETTING_HIDE_SHORTCUTS = "hide_menu_shortcuts"
SETTING_MENU_ANIMATION = "menu_animation"

MENU_NAMES = (
    "文件", "编辑", "视图", "图像", "图层", "选择",
    "滤镜", "工具", "设置", "窗口", "帮助",
)

# 内部中文名 -> 英文名（Krita 英文界面下回退匹配用）
_MENU_EN = {
    "文件": "File", "编辑": "Edit", "视图": "View", "图像": "Image",
    "图层": "Layer", "选择": "Select", "滤镜": "Filter", "工具": "Tools",
    "设置": "Settings", "窗口": "Window", "帮助": "Help",
}


def read_bool_setting(key, default=True):
    raw = Krita.instance().readSetting(
        SETTINGS_GROUP, key, "true" if default else "false"
    )
    return str(raw).lower() == "true"


def write_bool_setting(key, value):
    Krita.instance().writeSetting(
        SETTINGS_GROUP, key, "true" if value else "false"
    )


# ---- 菜单文本 / 显隐 ---------------------------------------------------

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
    for menu_name in MENU_NAMES:
        is_visible = read_bool_setting(f"show_{menu_name}", default=True)
        toggle_top_menu(qwin, menu_name, is_visible)


def apply_menu_text_settings(qwin):
    """应用菜单文本设置（是否隐藏快捷键提示）"""
    hide = read_bool_setting(SETTING_HIDE_SHORTCUTS, default=True)
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


# ---- DMS UI 菜单 -------------------------------------------------------

def setup_ui_settings(window, extension):
    """在菜单栏最右侧创建 DMS UI 菜单（每个窗口一个）"""
    qwin = window.qwindow()
    menubar = qwin.menuBar()

    # 多窗口安全：菜单挂在各自窗口的 menubar 下，用 objectName 判重
    if menubar.findChild(QMenu, "dms_menu") is not None:
        return

    dms_menu = menubar.addMenu("DMS UI")
    dms_menu.setObjectName("dms_menu")
    extension._dms_menu = dms_menu

    title_action = window.createAction("dms_menu_title", "--- 显示/隐藏顶部菜单 ---", "")
    title_action.setEnabled(False)
    dms_menu.addAction(title_action)

    for menu_name in MENU_NAMES:
        action = window.createAction(f"dms_toggle_{menu_name}", menu_name, "")
        action.setCheckable(True)
        action.setChecked(read_bool_setting(f"show_{menu_name}", default=True))
        action.toggled.connect(
            lambda checked, name=menu_name, q=qwin: on_menu_toggled(q, name, checked)
        )
        dms_menu.addAction(action)

    dms_menu.addSeparator()

    action_hide_shortcuts = window.createAction(
        "dms_hide_menu_shortcuts", "隐藏菜单栏快捷键提示", ""
    )
    action_hide_shortcuts.setCheckable(True)
    action_hide_shortcuts.setChecked(
        read_bool_setting(SETTING_HIDE_SHORTCUTS, default=True)
    )

    def on_shortcuts_toggled(checked, q=qwin):
        write_bool_setting(SETTING_HIDE_SHORTCUTS, checked)
        apply_menu_text_settings(q)

    action_hide_shortcuts.toggled.connect(on_shortcuts_toggled)
    dms_menu.addAction(action_hide_shortcuts)

    action_menu_animation = window.createAction(
        "dms_menu_animation", "菜单弹出动画", ""
    )
    action_menu_animation.setCheckable(True)
    action_menu_animation.setChecked(
        read_bool_setting(SETTING_MENU_ANIMATION, default=True)
    )

    def on_menu_animation_toggled(checked, ext=extension):
        write_bool_setting(SETTING_MENU_ANIMATION, checked)
        animator = getattr(ext, "menu_animator", None)
        if animator:
            animator.set_enabled(checked)

    action_menu_animation.toggled.connect(on_menu_animation_toggled)
    dms_menu.addAction(action_menu_animation)

    dms_menu.addSeparator()

    action_refresh = window.createAction("dms_refresh_theme", "🔄 重载当前主题色", "")
    action_refresh.triggered.connect(extension.refresh_theme)
    dms_menu.addAction(action_refresh)

    # 初次加载时应用一次
    apply_menu_text_settings(qwin)
    apply_menu_visibility_settings(qwin)


def on_menu_toggled(qwin, menu_name, checked):
    """当用户勾选/取消时触发"""
    toggle_top_menu(qwin, menu_name, checked)
    write_bool_setting(f"show_{menu_name}", checked)
