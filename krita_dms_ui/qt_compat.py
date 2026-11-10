"""Qt 绑定兼容层。

Krita 6 使用 PyQt6（作用域枚举，如 ``QEvent.Type.Polish``），
Krita 5 使用 PyQt5（类属性枚举，如 ``QEvent.Polish``）。

新增代码统一从这里导入 Qt 类和枚举常量，避免再出现
PyQt5 下访问 ``QEvent.Type`` 之类的 AttributeError。
"""

try:
    from PyQt6.QtCore import (
        QEasingCurve,
        QEvent,
        QObject,
        QPropertyAnimation,
        QTimer,
        Qt,
    )
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QGraphicsOpacityEffect,
        QLabel,
        QListWidget,
        QMenu,
        QMenuBar,
        QRadioButton,
        QWidget,
    )

    IS_QT6 = True
except ImportError:
    from PyQt5.QtCore import (
        QEasingCurve,
        QEvent,
        QObject,
        QPropertyAnimation,
        QTimer,
        Qt,
    )
    from PyQt5.QtGui import QColor, QPalette
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QGraphicsOpacityEffect,
        QLabel,
        QListWidget,
        QMenu,
        QMenuBar,
        QRadioButton,
        QWidget,
    )

    IS_QT6 = False


# ---- 枚举兼容 ----------------------------------------------------------
# PyQt6 的枚举是嵌套的（QPalette.ColorRole.Highlight），
# PyQt5 直接挂在类上（QPalette.Highlight）。
COLOR_ROLE = QPalette.ColorRole if IS_QT6 else QPalette
COLOR_GROUP = QPalette.ColorGroup if IS_QT6 else QPalette

POLISH_EVENT = QEvent.Type.Polish if IS_QT6 else QEvent.Polish
SHOW_EVENT = QEvent.Type.Show if IS_QT6 else QEvent.Show

WA_HOVER = Qt.WidgetAttribute.WA_Hover if IS_QT6 else Qt.WA_Hover
WA_STYLED_BACKGROUND = (
    Qt.WidgetAttribute.WA_StyledBackground if IS_QT6 else Qt.WA_StyledBackground
)
WA_TRANSLUCENT_BACKGROUND = (
    Qt.WidgetAttribute.WA_TranslucentBackground
    if IS_QT6
    else Qt.WA_TranslucentBackground
)

FRAMELESS_WINDOW_HINT = (
    Qt.WindowType.FramelessWindowHint if IS_QT6 else Qt.FramelessWindowHint
)
NO_DROP_SHADOW_WINDOW_HINT = (
    Qt.WindowType.NoDropShadowWindowHint if IS_QT6 else Qt.NoDropShadowWindowHint
)

EASING_OUT_CUBIC = QEasingCurve.Type.OutCubic if IS_QT6 else QEasingCurve.OutCubic
