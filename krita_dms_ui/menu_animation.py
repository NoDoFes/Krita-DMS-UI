"""动效层：DankMaterialShell / M3 动效 token + 菜单淡入。

动效参数优先从 DankMaterialShell 的 ``settings.json`` 读取，与 DMS 的
Material You 动效保持同一套节奏（曲线、时长、减少动态效果）；读不到时
退回 KDE 的 ``AnimationDurationFactor``，再退回内置默认值。

本模块不依赖 styles.py / hacks.py，可单独删除而不影响其他功能。
"""

import json
from pathlib import Path

from .qt_compat import (
    EASING_BEZIER,
    HIDE_EVENT,
    NO_FOCUS,
    POLISH_EVENT,
    POPUP_WINDOW,
    SHOW_EVENT,
    QEasingCurve,
    QGraphicsOpacityEffect,
    QLabel,
    QMenu,
    QObject,
    QPainter,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QStandardPaths,
    QWidget,
    SMOOTH_PIXMAP,
    STANDARD_PATH,
    TOOLTIP_WINDOW,
    WA_NO_SYSTEM_BACKGROUND,
    WA_TRANSPARENT_FOR_MOUSE,
)

# DMS 的默认值：settings.json 只保存被改过的键
_DMS_DEFAULTS = {
    "reduceMotion": False,
    "animationDuration": 250,
    "popoutAnimationDuration": 150,
    "interfaceStyle": "expressive",
}

# M3 / DMS 曲线（每段是三次贝塞尔的两个控制点 + 终点）
_CURVE_EXPRESSIVE_EFFECTS = ((0.34, 0.8), (0.34, 1.0), (1.0, 1.0))
_CURVE_STANDARD_DECEL = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0))
_CURVE_EXPRESSIVE_FAST_SPATIAL = ((0.42, 1.67), (0.21, 0.9), (1.0, 1.0))


def _curve(points):
    curve = QEasingCurve(EASING_BEZIER)
    curve.addCubicBezierSegment(
        QPointF(*points[0]), QPointF(*points[1]), QPointF(*points[2])
    )
    return curve


class Motion:
    """一次读取得到的动效参数（单位：毫秒）。"""

    __slots__ = (
        "enabled",
        "reduce_motion",
        "popup_duration",
        "effects_duration",
        "spatial_duration",
        "effects_curve",
        "spatial_curve",
        "source",
    )

    def __init__(
        self,
        enabled,
        reduce_motion,
        popup_duration,
        effects_duration,
        spatial_duration,
        effects_curve,
        spatial_curve,
        source,
    ):
        self.enabled = enabled
        self.reduce_motion = reduce_motion
        self.popup_duration = popup_duration
        self.effects_duration = effects_duration
        self.spatial_duration = spatial_duration
        self.effects_curve = effects_curve
        self.spatial_curve = spatial_curve
        self.source = source


def _load_json(path):
    """读 DMS 设置；文件缺失或解析失败返回 None（走 KDE / 默认值）。"""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _number(value, default):
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _config_home():
    base = QStandardPaths.writableLocation(STANDARD_PATH.GenericConfigLocation)
    return Path(base) if base else Path.home() / ".config"


def _dms_settings_path():
    home = _config_home()
    for name in ("dms", "DankMaterialShell"):
        candidate = home / name / "settings.json"
        if candidate.is_file():
            return candidate
    return None


def _kde_duration_factor(path=None):
    """读取 ``kdeglobals`` 的 ``[KDE] AnimationDurationFactor``。

    0 表示关闭动画，1 正常，>1 更慢。文件不存在返回 None。
    """
    path = Path(path) if path else _config_home() / "kdeglobals"
    section = None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None

    for line in lines:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if section != "KDE" or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "AnimationDurationFactor":
            continue
        try:
            return float(value.split(";")[0].strip())
        except ValueError:
            return None
    return None


def read_motion(dms_path=None, kde_path=None):
    """读取当前应使用的动效参数。

    ``dms_path`` / ``kde_path`` 仅用于测试；正常调用走系统路径。
    """
    path = Path(dms_path) if dms_path else _dms_settings_path()
    data = _load_json(path) if path else None

    if data is not None:
        reduce_motion = bool(data.get("reduceMotion", _DMS_DEFAULTS["reduceMotion"]))
        base = max(0.0, _number(data.get("animationDuration"), _DMS_DEFAULTS["animationDuration"]))
        popup = max(0.0, _number(data.get("popoutAnimationDuration"), _DMS_DEFAULTS["popoutAnimationDuration"]))
        classic = str(data.get("interfaceStyle", _DMS_DEFAULTS["interfaceStyle"])) == "classic"
        enabled = not reduce_motion and base > 0 and popup > 0
        return Motion(
            enabled=enabled,
            reduce_motion=reduce_motion,
            popup_duration=round(popup) if enabled else 0,
            effects_duration=round(base * 0.4) if base > 0 and not reduce_motion else 0,
            spatial_duration=round(base * 0.7) if base > 0 and not reduce_motion else 0,
            effects_curve=_curve(_CURVE_STANDARD_DECEL if classic else _CURVE_EXPRESSIVE_EFFECTS),
            spatial_curve=_curve(_CURVE_STANDARD_DECEL if classic else _CURVE_EXPRESSIVE_FAST_SPATIAL),
            source="dms",
        )

    factor = _kde_duration_factor(kde_path)
    if factor is not None:
        if factor <= 0:
            return Motion(
                enabled=False,
                reduce_motion=True,
                popup_duration=0,
                effects_duration=0,
                spatial_duration=0,
                effects_curve=_curve(_CURVE_STANDARD_DECEL),
                spatial_curve=_curve(_CURVE_STANDARD_DECEL),
                source="kde",
            )
        factor = min(max(factor, 0.25), 2.0)
        return Motion(
            enabled=True,
            reduce_motion=False,
            popup_duration=round(150 * factor),
            effects_duration=round(200 * factor),
            spatial_duration=round(250 * factor),
            effects_curve=_curve(_CURVE_EXPRESSIVE_EFFECTS),
            spatial_curve=_curve(_CURVE_EXPRESSIVE_FAST_SPATIAL),
            source="kde",
        )

    return Motion(
        enabled=True,
        reduce_motion=False,
        popup_duration=150,
        effects_duration=200,
        spatial_duration=250,
        effects_curve=_curve(_CURVE_EXPRESSIVE_EFFECTS),
        spatial_curve=_curve(_CURVE_EXPRESSIVE_FAST_SPATIAL),
        source="default",
    )


class _MenuFadeOverlay(QWidget):
    """菜单隐藏后，用最后一帧截图在主窗口里淡出。

    QMenu 是原生 popup，Qt 在发出 ``aboutToHide`` 之前就已经把窗口
    取消映射了，插件没法延迟 ``hide()``。所以只能截一帧盖在主窗口上。
    覆盖层是主窗口的子控件，超出窗口的部分会被裁掉。
    """

    def __init__(self, parent, pixmap):
        super().__init__(parent)
        self._pixmap = pixmap
        self.setAttribute(WA_TRANSPARENT_FOR_MOUSE, True)
        self.setAttribute(WA_NO_SYSTEM_BACKGROUND, True)
        self.setFocusPolicy(NO_FOCUS)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(SMOOTH_PIXMAP, True)
        painter.drawPixmap(0, 0, self._pixmap)


class MenuAnimator(QObject):
    """监听菜单弹出，给菜单 / 下拉列表做淡入淡出。"""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._enabled = True
        self._motion = read_motion()
        self._animations = {}
        self._effects = {}
        self._pending_in = {}
        self._fade_outs = {}

    def install(self):
        """挂到 QApplication 上；重复调用不会重复安装。"""
        if self.app is None:
            return

        self.app.installEventFilter(self)

        # 插件加载时已经存在的菜单也补挂一次（有些菜单可能早已 Polish 过）
        for widget in self.app.allWidgets():
            if isinstance(widget, QMenu):
                self._hook_menu(widget)

    def set_enabled(self, enabled):
        """用户开关（DMS UI 菜单）；与 DMS 的 reduceMotion 是「与」的关系。"""
        self._enabled = bool(enabled)
        if not self._enabled:
            self._stop_all()

    def refresh_motion(self):
        """重新读取 DMS / KDE 动效参数（主题重载或新窗口时调用）。"""
        self._motion = read_motion()
        if not self._motion.enabled:
            self._stop_all()
        return self._motion

    def _stop_all(self):
        for anim in list(self._animations.values()):
            anim.stop()
        self._animations.clear()
        self._pending_in.clear()
        self._clear_fade_outs()

        # 关闭时把残留的半透明效果复位，避免菜单变灰
        for effect in list(self._effects.values()):
            try:
                effect.setOpacity(1.0)
            except RuntimeError:
                pass

    def eventFilter(self, obj, event):
        event_type = event.type()

        # QToolTip 的标签是 Qt.ToolTip 类型的 QLabel，做一次短淡入
        if isinstance(obj, QLabel) and obj.windowType() == TOOLTIP_WINDOW:
            if event_type == SHOW_EVENT:
                motion = self._motion
                duration = motion.effects_duration or motion.popup_duration
                self._fade_in(obj, duration, motion.effects_curve)
            return False

        # QComboBox 的弹出列表是 QComboBoxPrivateContainer（QFrame）
        if event_type == SHOW_EVENT and obj.metaObject().className() == "QComboBoxPrivateContainer":
            motion = self._motion
            duration = motion.effects_duration or motion.popup_duration
            self._fade_in(obj, duration, motion.effects_curve)
            return False

        if not isinstance(obj, QMenu):
            return False

        if event_type == POLISH_EVENT:
            self._hook_menu(obj)
        elif event_type == SHOW_EVENT:
            # 有些菜单（例如很长的面板列表）在 aboutToShow 里做布局，
            # 动画如果在那里启动，窗口真正出现时已经跑完了。
            # 统一等到 Show 再启动。
            self._hook_menu(obj)
            self._show_menu(obj)
        elif event_type == HIDE_EVENT:
            self._pending_in.pop(obj, None)
        return False

    def _hook_menu(self, menu):
        if menu.property("dms_anim_hooked"):
            return
        menu.setProperty("dms_anim_hooked", True)
        menu.aboutToShow.connect(lambda m=menu: self._queue_menu_in(m))
        menu.aboutToHide.connect(lambda m=menu: self._animate_out(m))
        self._ensure_cleanup(menu)

    def _ensure_cleanup(self, widget):
        """控件销毁后清掉引用，避免 _animations / _effects 长期持有失效对象。"""
        if widget.property("dms_cleanup_hooked"):
            return
        widget.setProperty("dms_cleanup_hooked", True)
        widget.destroyed.connect(lambda _=None, w=widget: self._forget(w))

    def _forget(self, widget):
        self._animations.pop(widget, None)
        self._effects.pop(widget, None)
        self._pending_in.pop(widget, None)
        overlay = self._fade_outs.pop(widget, None)
        if overlay is not None:
            try:
                overlay.deleteLater()
            except RuntimeError:
                pass

    def _effect_for(self, menu):
        effect = self._effects.get(menu)
        if effect is not None:
            return effect

        effect = menu.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(menu)
            menu.setGraphicsEffect(effect)

        self._effects[menu] = effect
        return effect

    def _fade_params(self, menu):
        motion = self._motion
        if not self._enabled or not motion.enabled or motion.popup_duration <= 0:
            return None

        # 子菜单出现频率高，用 effects 的短时长；顶层 / 右键菜单用 popup 时长
        duration = motion.popup_duration
        if isinstance(menu.parentWidget(), QMenu):
            duration = min(duration, motion.effects_duration or duration)
        return duration, motion.effects_curve

    def _queue_menu_in(self, menu):
        """aboutToShow 只负责把透明度置零，动画等 Show 再启动。"""
        params = self._fade_params(menu)
        if params is None:
            return
        self._effect_for(menu).setOpacity(0.0)
        self._pending_in[menu] = params

    def _show_menu(self, menu):
        params = self._pending_in.pop(menu, None)
        if params is None:
            params = self._fade_params(menu)
            if params is None:
                return
            # 没走 aboutToShow 的菜单，在 Show 时补一次置零
            self._effect_for(menu).setOpacity(0.0)
        self._fade_in(menu, *params)

    @staticmethod
    def _host_window(menu):
        """菜单所属的普通顶层窗口（跳过 QMenu / ToolTip 这些 popup）。"""
        parent = menu.parentWidget()
        while parent is not None:
            if parent.isWindow() and parent.windowType() not in (POPUP_WINDOW, TOOLTIP_WINDOW):
                return parent
            parent = parent.parentWidget()
        return None

    def _animate_out(self, menu):
        """菜单隐藏后做淡出；用截图覆盖层是因为 QMenu 已经先被取消映射。"""
        motion = self._motion
        if not self._enabled or not motion.enabled:
            return
        if menu in self._fade_outs:
            return
        if self.app is None or self.app.closingDown():
            return

        host = self._host_window(menu)
        if host is None or not host.isVisible():
            return

        # 菜单可能在淡入到一半时就被关闭：截图前先把效果暂时拉满，
        # 否则覆盖层会是一张半透明的残影。
        effect = menu.graphicsEffect()
        previous_opacity = None
        if isinstance(effect, QGraphicsOpacityEffect):
            previous_opacity = effect.opacity()
            effect.setOpacity(1.0)
        pixmap = menu.grab()
        if previous_opacity is not None:
            try:
                effect.setOpacity(previous_opacity)
            except RuntimeError:
                pass
        if pixmap.isNull():
            return

        pos = host.mapFromGlobal(menu.mapToGlobal(QPoint(0, 0)))
        if not host.rect().intersects(QRect(pos, menu.size())):
            return

        overlay = _MenuFadeOverlay(host, pixmap)
        overlay.setGeometry(pos.x(), pos.y(), menu.width(), menu.height())
        overlay.show()
        overlay.raise_()

        duration = motion.effects_duration or 100
        effect = QGraphicsOpacityEffect(overlay)
        overlay.setGraphicsEffect(effect)
        effect.setOpacity(1.0)

        anim = QPropertyAnimation(effect, b"opacity", overlay)
        anim.setDuration(max(60, duration))
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(motion.effects_curve)
        anim.finished.connect(lambda m=menu: self._remove_fade_out(m))

        self._fade_outs[menu] = overlay
        anim.start()

    def _remove_fade_out(self, menu):
        overlay = self._fade_outs.pop(menu, None)
        if overlay is not None:
            try:
                overlay.deleteLater()
            except RuntimeError:
                pass

    def _clear_fade_outs(self):
        for overlay in self._fade_outs.values():
            try:
                overlay.setParent(None)
                overlay.deleteLater()
            except RuntimeError:
                pass
        self._fade_outs.clear()

    def _fade_in(self, widget, duration, curve):
        """通用淡入：菜单与 tooltip 共用，效果对象按控件缓存。"""
        if not self._enabled or not self._motion.enabled or duration <= 0:
            return

        self._ensure_cleanup(widget)
        old = self._animations.pop(widget, None)
        if old is not None:
            old.stop()

        effect = self._effect_for(widget)

        # aboutToShow / Show 在窗口显示前触发，先置零可以避免第一帧闪烁
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(curve)
        anim.finished.connect(lambda w=widget: self._finish(w))

        # 持有引用，防止动画对象被 Python 提前回收
        self._animations[widget] = anim
        anim.start()

    def _finish(self, menu):
        self._animations.pop(menu, None)
        effect = self._effects.get(menu)
        try:
            if effect is not None:
                effect.setOpacity(1.0)
        except RuntimeError:
            # 菜单可能在动画期间被销毁
            self._effects.pop(menu, None)
