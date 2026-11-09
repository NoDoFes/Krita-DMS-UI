try:
    from PyQt6.QtGui import QColor
except ImportError:
    from PyQt5.QtGui import QColor

MODERN_QSS = """
/* ================== DMS 动态高对比度实色版 ================== */

/* ====== 顶部菜单栏 ====== */
QMenuBar { background-color: {{BG}}; border: none; padding: 4px 8px; }
QMenuBar::item { 
    background-color: {{ITEM_BG}}; 
    padding: 6px 14px; 
    margin: 2px 4px;   
    border-radius: 6px; 
    color: {{TEXT}} !important; 
}
QMenuBar::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QMenuBar::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }

QMainWindow::separator { background-color: {{BG}}; width: 0px; height: 0px; }
QSplitter::handle { background-color: {{BG}}; }

/* ====== 工具栏 ====== */
QToolBar { 
    background-color: {{BG}}; 
    border: none; 
    spacing: 4px; 
    padding: 4px; 
}
QToolBar::separator {
    background-color: {{BORDER}};
    width: 1px;
    margin: 4px 6px;
}
QToolBar QToolButton { 
    background-color: {{ITEM_BG}}; 
    border: none; 
    border-radius: 6px; 
    padding: 4px; 
    margin: 2px;
    color: {{TEXT}} !important; 
}
QToolBar QToolButton:hover { 
    background-color: {{HOVER_BG}}; 
}
QToolBar QToolButton:pressed, QToolBar QToolButton:checked { 
    background-color: {{SELECT_BG}}; 
    color: {{HIGHLIGHT_TEXT}} !important; 
}

/* ====== 弹出菜单 ====== */
QMenu { background-color: {{BASE_BG}}; border: 1px solid {{BORDER}}; border-radius: 8px; padding: 6px; outline: none; }
QMenu::item { background-color: transparent; padding: 6px 24px 6px 12px; border-radius: 6px; color: {{TEXT}} !important; }
QMenu::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QMenu::item:disabled { color: {{TEXT_DISABLED}} !important; background-color: transparent !important; }

/* ====== 停靠窗口 & 标签页 ====== */
QDockWidget { border: none; margin: 0px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 0px; margin: 0px; }

QTabWidget { border: none; background: {{BG}}; }
QTabWidget::pane { border: none; background: {{BG}}; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

QTabBar { background: transparent; border: none; qproperty-drawBase: 0; }
QTabBar::tab { 
    background: transparent; border: none; padding: 6px 20px; margin: 4px 4px 0px 4px; 
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;
    color: {{TEXT}} !important; 
}
QTabBar::tab:hover:!selected { background-color: {{HOVER_BG}}; border-bottom: 1px solid {{HOVER_BG}}; color: {{TEXT}} !important; }
QTabBar::tab:selected { background-color: {{SELECT_BG}}; border-bottom: 1px solid {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }

QTabBar::close-button { subcontrol-origin: padding; subcontrol-position: center right; margin-right: 6px; width: 16px; height: 16px; border-radius: 8px; background: transparent; }
QTabBar::close-button:hover { background-color: rgba(255, 80, 80, 0.3); }

/* ====== 列表 / 树（通用面板：图层、笔刷等） ====== */
QTreeView, QListView, QListWidget { background-color: {{BG}}; border: none; outline: none; show-decoration-selected: 1; }
QTreeView::item, QListView::item, QListWidget::item { 
    border-radius: 6px; 
    padding: 4px; 
    margin: 2px 0px; 
    color: {{TEXT}} !important; 
}
QTreeView::item:hover:!selected, QListView::item:hover:!selected, QListWidget::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QTreeView::item:selected, QListView::item:selected, QListWidget::item:selected { background-color: {{SELECT_BG}} !important; color: {{HIGHLIGHT_TEXT}} !important; }

/* ====== 特殊修补：配置窗口左侧 ====== */
/* 给外层容器加左右留白，强行把里面的高亮框挤出来，防止贴边 */
KisConfigView, QDialog QListView {
    padding: 0px 6px !important;
}
/* 缩小内边距，让上下更加紧凑 */
KisConfigView::item, QDialog QListView::item { 
    border-radius: 6px !important; 
    padding: 2px 4px !important; 
    margin: 2px 0px !important; 
    color: {{TEXT}} !important; 
}
KisConfigView::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
KisConfigView::item:selected { background-color: {{SELECT_BG}} !important; color: {{HIGHLIGHT_TEXT}} !important; }

/* ====== 按钮 ====== */
QPushButton { background-color: {{BASE_BG}}; border: none; border-radius: 6px; padding: 5px 12px; color: {{TEXT}} !important; }
QPushButton:hover { background-color: {{HOVER_BG}}; }
QPushButton:pressed { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QPushButton:disabled { color: {{TEXT_DISABLED}} !important; background-color: {{BG}} !important; }

/* ====== 输入框 & 下拉框 ====== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, KisDoubleSliderSpinBox, KisSliderSpinBox { 
    background-color: {{ITEM_BG}}; 
    border: 1px solid transparent; 
    border-radius: 6px; 
    padding: 4px 8px; 
    color: {{TEXT}} !important; 
    selection-background-color: {{SELECT_BG}};
    selection-color: {{HIGHLIGHT_TEXT}};
}
QSpinBox, QDoubleSpinBox { padding-right: 20px; }

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover, KisDoubleSliderSpinBox:hover, KisSliderSpinBox:hover { 
    background-color: {{HOVER_BG}}; 
    color: {{TEXT}} !important; 
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, KisDoubleSliderSpinBox:focus, KisSliderSpinBox:focus { 
    background-color: {{ITEM_BG}}; 
    color: {{TEXT}} !important; 
    border: 1px solid {{SELECT_BG}}; 
}

QSpinBox QLineEdit, QDoubleSpinBox QLineEdit { 
    background: transparent; 
    color: {{TEXT}} !important; 
    selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}};
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; 
    subcontrol-position: top right; 
    width: 16px;
    border-top-right-radius: 4px; 
    background-color: rgba(128, 128, 128, 40);
    border-left: 1px solid {{BORDER}}; 
    margin-top: 2px; 
    margin-right: 2px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; 
    subcontrol-position: bottom right; 
    width: 16px;
    border-bottom-right-radius: 4px; 
    background-color: rgba(128, 128, 128, 40);
    border-left: 1px solid {{BORDER}}; 
    margin-bottom: 2px; 
    margin-right: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { 
    background-color: rgba(128, 128, 128, 90); 
}

QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background-color: {{BASE_BG}}; border: 1px solid {{BORDER}}; border-radius: 6px; selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}} !important; color: {{TEXT}} !important; }

/* ====== 滚动条 ====== */
QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: {{MID_BG}}; min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: {{SELECT_BG}}; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; border: none; height: 0px; }
"""

def get_theme_colors(palette, COLOR_ROLE):
    bg_color = palette.color(COLOR_ROLE.Window)
    base_color = palette.color(COLOR_ROLE.Base)
    mid_color = palette.color(COLOR_ROLE.Mid)
    highlight_color = palette.color(COLOR_ROLE.Highlight)
    
    is_light = bg_color.lightness() >= 128
    
    if not is_light:
        text_color = "#cccccc"
        text_disabled = "#666666"
        hover_bg = "#2e2e2e"
        border_color = "rgba(255, 255, 255, 15)"
        item_bg = "rgba(255, 255, 255, 15)"
    else:
        text_color = "#333333"
        text_disabled = "#aaaaaa"
        hover_bg = "#ebebeb"
        border_color = "rgba(0, 0, 0, 20)"
        item_bg = "rgba(0, 0, 0, 15)"

    highlight_text = "#000000" if highlight_color.lightness() > 130 else "#ffffff"

    return {
        "BG": bg_color.name(),
        "BASE_BG": base_color.name(),
        "MID_BG": mid_color.name(),
        "ITEM_BG": item_bg,
        "TEXT": text_color,
        "TEXT_DISABLED": text_disabled,
        "HOVER_BG": hover_bg,
        "SELECT_BG": highlight_color.name(),
        "HIGHLIGHT_TEXT": highlight_text,
        "BORDER": border_color
    }

def build_qss(colors):
    return MODERN_QSS.replace("{{TEXT}}", colors["TEXT"])\
                     .replace("{{TEXT_DISABLED}}", colors["TEXT_DISABLED"])\
                     .replace("{{HOVER_BG}}", colors["HOVER_BG"])\
                     .replace("{{SELECT_BG}}", colors["SELECT_BG"])\
                     .replace("{{BORDER}}", colors["BORDER"])\
                     .replace("{{HIGHLIGHT_TEXT}}", colors["HIGHLIGHT_TEXT"])\
                     .replace("{{BG}}", colors["BG"])\
                     .replace("{{BASE_BG}}", colors["BASE_BG"])\
                     .replace("{{MID_BG}}", colors["MID_BG"])\
                     .replace("{{ITEM_BG}}", colors["ITEM_BG"])