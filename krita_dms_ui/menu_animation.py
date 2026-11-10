"""顶部菜单弹出动画（Material You 3 最小实现）。

Krita 的菜单是原生 ``QMenu`` 弹出窗口。Qt 的 Wayland 平台插件不支持
``setWindowOpacity``（空实现），所以在 Wayland 下动画会失效。

这里改用 ``QGraphicsOpacityEffect``：透明度作用在菜单自己的渲染缓冲上，
不依赖合成器的窗口透明度支持，X11 / Wayland 都能生效。

当前范围（刻意保持最小）：
- 只处理从菜单栏展开的顶层菜单（文件 / 编辑 / 视图 ...）
- 不处理右键菜单和子菜单
- 只做淡入，不做位移 / 缩放 / 退出动画

本模块不依赖 styles.py / hacks.py，可单独删除而不影响其他功能。
"""

from .qt_compat import (
    EASING_OUT_CUBIC,
    POLISH_EVENT,
    SHOW_EVENT,
    QGraphicsOpacityEffect,
    QMenu,
    QMenuBar,
    QObject,
    QPropertyAnimation,
)


class MenuAnimator(QObject):
    """监听菜单弹出，给菜单栏下拉做淡入过渡。"""

    # Material You 3 的 short4 时长，配合 decelerate 曲线
    DURATION_MS = 200

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._enabled = True
        self._animations = {}
        self._effects = {}

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
        self._enabled = bool(enabled)
        if not self._enabled:
            for anim in list(self._animations.values()):
                anim.stop()
            self._animations.clear()

            # 关闭时把残留的半透明效果复位，避免菜单变灰
            for effect in list(self._effects.values()):
                try:
                    effect.setOpacity(1.0)
                except RuntimeError:
                    pass

    def eventFilter(self, obj, event):
        if not isinstance(obj, QMenu):
            return False

        event_type = event.type()
        if event_type == POLISH_EVENT:
            self._hook_menu(obj)
        elif event_type == SHOW_EVENT:
            # 如果菜单在过滤器安装前就 Polish 过，Show 时补挂并补一次动画
            first_time = not obj.property("dms_anim_hooked")
            self._hook_menu(obj)
            if first_time:
                self._animate_in(obj)
        return False

    def _hook_menu(self, menu):
        if menu.property("dms_anim_hooked"):
            return
        menu.setProperty("dms_anim_hooked", True)
        menu.aboutToShow.connect(lambda m=menu: self._animate_in(m))

    @staticmethod
    def _is_menu_bar_menu(menu):
        """只给菜单栏下拉做动画，避开右键菜单和子菜单。

        QMenu 是独立的弹出窗口，``parentWidget`` 不一定就是 QMenuBar
        （Krita 可能先以主窗口为父创建菜单，再挂到菜单栏），所以优先用
        QAction 的关联对象判断，再回退到父级查找。
        """
        menu_action = menu.menuAction()

        associated = getattr(menu_action, "associatedObjects", None)
        if associated is not None:
            return any(isinstance(obj, QMenuBar) for obj in associated())

        parent = menu.parentWidget()
        if isinstance(parent, QMenuBar):
            return True
        if parent is not None:
            menu_bar = parent.window().findChild(QMenuBar)
            return menu_bar is not None and menu_action in menu_bar.actions()
        return False

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

    def _animate_in(self, menu):
        if not self._enabled or not self._is_menu_bar_menu(menu):
            return

        old = self._animations.pop(menu, None)
        if old is not None:
            old.stop()

        effect = self._effect_for(menu)

        # aboutToShow 在窗口显示前触发，先置零可以避免第一帧闪烁
        effect.setOpacity(0.0)

        anim = QPropertyAnimation(effect, b"opacity", menu)
        anim.setDuration(self.DURATION_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(EASING_OUT_CUBIC)
        anim.finished.connect(lambda m=menu: self._finish(m))

        # 持有引用，防止动画对象被 Python 提前回收
        self._animations[menu] = anim
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
