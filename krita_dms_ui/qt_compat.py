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
        QPointF,
        QPropertyAnimation,
        QRectF,
        QTimer,
        Qt,
    )
    from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QGraphicsOpacityEffect,
        QLabel,
        QListView,
        QListWidget,
        QMenu,
        QMenuBar,
        QProxyStyle,
        QRadioButton,
        QStyle,
        QWidget,
    )

    IS_QT6 = True
except ImportError:
    from PyQt5.QtCore import (
        QEasingCurve,
        QEvent,
        QObject,
        QPointF,
        QPropertyAnimation,
        QRectF,
        QTimer,
        Qt,
    )
    from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QGraphicsOpacityEffect,
        QLabel,
        QListView,
        QListWidget,
        QMenu,
        QMenuBar,
        QProxyStyle,
        QRadioButton,
        QStyle,
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

# ---- QStyle：自绘 indicator 用到的枚举 ----
PIXEL_METRIC = QStyle.PixelMetric if IS_QT6 else QStyle
PRIMITIVE_ELEMENT = QStyle.PrimitiveElement if IS_QT6 else QStyle
STATE_FLAG = QStyle.StateFlag if IS_QT6 else QStyle

ANTIALIASING = QPainter.RenderHint.Antialiasing if IS_QT6 else QPainter.Antialiasing
NO_PEN = Qt.PenStyle.NoPen if IS_QT6 else Qt.NoPen
NO_BRUSH = Qt.BrushStyle.NoBrush if IS_QT6 else Qt.NoBrush
ROUND_CAP = Qt.PenCapStyle.RoundCap if IS_QT6 else Qt.RoundCap
ROUND_JOIN = Qt.PenJoinStyle.RoundJoin if IS_QT6 else Qt.RoundJoin

# ---- sip：判断 C++ 对象是否已被 Qt 销毁（样式被 Krita 换掉时用） ----
try:
    from PyQt6 import sip
except ImportError:
    from PyQt5 import sip
