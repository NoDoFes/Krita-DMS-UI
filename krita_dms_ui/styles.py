try:
    from PyQt6.QtGui import QColor
except ImportError:
    from PyQt5.QtGui import QColor

MODERN_QSS = """
/* ================== DMS 动态高对比度实色版 ================== */

QMenuBar { background-color: palette(window); border: none; padding: 2px; }
QMenuBar::item { background: transparent; padding: 8px 20px; border-radius: 8px; margin: 0px 2px; color: {{TEXT}} !important; }
QMenuBar::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QMenuBar::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }

QMainWindow::separator { background-color: palette(window); width: 0px; height: 0px; }
QSplitter::handle { background-color: palette(window); }

QMenu { background-color: palette(base); border: 1px solid {{BORDER}}; border-radius: 8px; padding: 6px; }
QMenu::item { background-color: transparent; padding: 6px 24px 6px 12px; border-radius: 6px; color: {{TEXT}} !important; }
QMenu::item:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QMenu::item:disabled { color: {{TEXT_DISABLED}} !important; background-color: transparent !important; }

QDockWidget { border: none; margin: 4px; titlebar-close-icon: url(none); titlebar-normal-icon: url(none); }
QDockWidget::title { background: transparent; padding: 6px; margin-top: 4px; }

QTabBar { background: transparent; border: none; }
QTabBar::tab { background: transparent; border: none; padding: 6px 28px 6px 12px; margin-right: 4px; border-radius: 6px; color: {{TEXT}} !important; }
QTabBar::tab:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QTabBar::tab:selected { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QTabWidget::pane { border: none; border-top: 0px; background: palette(window); top: -2px; margin-top: -1px; }
QTabWidget > QFrame { border: none; }

QTabBar::close-button { subcontrol-origin: padding; subcontrol-position: center right; margin-right: 6px; width: 16px; height: 16px; border-radius: 8px; background: transparent; }
QTabBar::close-button:hover { background-color: rgba(255, 80, 80, 0.3); }

/* ====== 列表 / 树（图层，强化伪状态覆盖） ====== */
QTreeView, QListView, QListWidget { background-color: palette(window); border: none; outline: none; show-decoration-selected: 1; }
QTreeView::item, QListView::item, QListWidget::item { border-radius: 6px; padding: 4px; margin: 2px 0px; color: {{TEXT}} !important; }
QTreeView::item:hover:!selected, QListView::item:hover:!selected, QListWidget::item:hover:!selected { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
QTreeView::item:selected, QTreeView::item:selected:active, QTreeView::item:selected:!active,
QListView::item:selected, QListView::item:selected:active, QListView::item:selected:!active,
QListWidget::item:selected, QListWidget::item:selected:active, QListWidget::item:selected:!active { background-color: {{SELECT_BG}} !important; color: {{HIGHLIGHT_TEXT}} !important; }

QPushButton { background-color: palette(button); border: none; border-radius: 6px; padding: 5px 12px; color: {{TEXT}} !important; }
QPushButton:hover { background-color: {{HOVER_BG}}; }
QPushButton:pressed { background-color: {{SELECT_BG}}; color: {{HIGHLIGHT_TEXT}} !important; }
QPushButton:disabled { color: {{TEXT_DISABLED}} !important; background-color: palette(window) !important; }

/* ====== 输入框（取消拖拽满屏高亮） ====== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { 
    background-color: palette(base); border: none; border-radius: 6px; padding: 4px 8px; 
    color: {{TEXT}} !important; 
    selection-background-color: {{SELECT_BG}};
    selection-color: {{HIGHLIGHT_TEXT}};
}
/* 给右侧微缩按钮留出位置 */
QSpinBox, QDoubleSpinBox { padding-right: 20px; }
/* 悬浮轻微高亮 */
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; }
/* 取消 focus 满屏高亮，用细边框提示 */
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { background-color: {{HOVER_BG}}; color: {{TEXT}} !important; border: 1px solid {{SELECT_BG}}; }

QSpinBox QLineEdit, QDoubleSpinBox QLineEdit { 
    background: transparent; color: {{TEXT}} !important; 
    selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}};
}

/* --- SpinBox 上下调节小模块美化（无 SVG） --- */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right; width: 16px;
    border-top-right-radius: 4px; background-color: rgba(128, 128, 128, 40);
    border-left: 1px solid {{BORDER}}; margin-top: 2px; margin-right: 2px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right; width: 16px;
    border-bottom-right-radius: 4px; background-color: rgba(128, 128, 128, 40);
    border-left: 1px solid {{BORDER}}; margin-bottom: 2px; margin-right: 2px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background-color: rgba(128, 128, 128, 90); }

QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView { background-color: palette(base); border: 1px solid {{BORDER}}; border-radius: 6px; selection-background-color: {{SELECT_BG}}; selection-color: {{HIGHLIGHT_TEXT}} !important; color: {{TEXT}} !important; }

QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
QScrollBar::handle:vertical { background: palette(mid); min-height: 30px; border-radius: 4px; }
QScrollBar::handle:vertical:hover { background: palette(highlight); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical, QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; border: none; height: 0px; }
"""

def get_theme_colors(palette, COLOR_ROLE):
    bg_color = palette.color(COLOR_ROLE.Window)
    matugen_highlight = palette.color(COLOR_ROLE.Highlight)
    
    is_light = bg_color.lightness() >= 128
    h, s, l, a = matugen_highlight.getHsl()
    
    if not is_light:
        select_color = QColor.fromHsl(h, int(s * 0.6), 80)
        text_color = "#cccccc"
        text_disabled = "#666666"
        hover_bg = "#2e2e2e"
        border_color = "rgba(255, 255, 255, 15)"
    else:
        select_color = QColor.fromHsl(h, int(s * 0.4), 220)
        text_color = "#333333"
        text_disabled = "#aaaaaa"
        hover_bg = "#ebebeb"
        border_color = "rgba(0, 0, 0, 20)"

    # 终极对比度判定：如果高亮背景偏亮，就用黑字
    highlight_text = "#000000" if select_color.lightness() > 130 else "#ffffff"

    return {
        "TEXT": text_color,
        "TEXT_DISABLED": text_disabled,
        "HOVER_BG": hover_bg,
        "SELECT_BG": select_color.name(),
        "HIGHLIGHT_TEXT": highlight_text,
        "BORDER": border_color
    }

def build_qss(colors):
    return MODERN_QSS.replace("{{TEXT}}", colors["TEXT"])\
                     .replace("{{TEXT_DISABLED}}", colors["TEXT_DISABLED"])\
                     .replace("{{HOVER_BG}}", colors["HOVER_BG"])\
                     .replace("{{SELECT_BG}}", colors["SELECT_BG"])\
                     .replace("{{BORDER}}", colors["BORDER"])\
                     .replace("{{HIGHLIGHT_TEXT}}", colors["HIGHLIGHT_TEXT"])