import weakref

from PySide6.QtWidgets import QApplication, QCheckBox
from PySide6.QtGui import (
    QPalette,
    QColor,
    QFont,
    QKeySequence,
    QShortcut,
    QPainter,
    QPen,
    QBrush,
)
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    Property,
    QRectF,
    QPointF,
    QAbstractAnimation,
    Signal,
    QObject,
)


class _FontScaleBus(QObject):
    fontScaleChanged = Signal(float)


class _ThemeBus(QObject):
    themeChanged = Signal(str)


_font_bus = _FontScaleBus()
_theme_bus = _ThemeBus()


def _clamp_font_scale(value: float) -> float:
    try:
        num = float(value)
    except Exception:
        num = 1.0
    return max(0.8, min(1.6, num))


def current_font_scale(app: QApplication) -> float:
    scale = app.property("font_scale")
    if scale is None:
        scale = 1.0
        app.setProperty("font_scale", scale)
    return _clamp_font_scale(scale)


def font_scale_signal():
    return _font_bus.fontScaleChanged


def theme_changed_signal():
    return _theme_bus.themeChanged


def set_font_scale(app: QApplication, scale: float) -> None:
    scale = _clamp_font_scale(scale)
    if current_font_scale(app) == scale:
        return
    app.setProperty("font_scale", scale)
    apply_theme(app, current_mode(app))
    font_scale_signal().emit(scale)


def _scaled_px(base: int, scale: float) -> int:
    return max(8, int(round(base * scale)))


def current_font_family(app: QApplication) -> str:
    family = app.property("font_family")
    if not family:
        family = "Segoe UI"
        app.setProperty("font_family", family)
    return str(family)


def set_font_family(app: QApplication, family: str) -> None:
    family = str(family or "Segoe UI")
    if current_font_family(app) == family:
        return
    app.setProperty("font_family", family)
    apply_theme(app, current_mode(app))


def bind_font_scale(widget, updater):
    """Registra una función que se invocará cuando cambie el escalado."""
    ref = weakref.ref(widget)

    def _wrapped(scale):
        obj = ref()
        if obj is None:
            try:
                font_scale_signal().disconnect(_wrapped)
            except Exception:
                pass
            return
        updater(obj, scale)

    font_scale_signal().connect(_wrapped)

    def _cleanup(*_args):
        try:
            font_scale_signal().disconnect(_wrapped)
        except Exception:
            pass

    widget.destroyed.connect(_cleanup)
    updater(widget, current_font_scale(QApplication.instance()))


def bind_font_scale_stylesheet(widget, template: str, **size_map: int):
    """Aplica una hoja de estilo con tamaños escalables.

    template debe contener placeholders {nombre}px; size_map asocia nombre->tamaño base.
    """

    def _apply(w, scale):
        values = {name: _scaled_px(base, scale) for name, base in size_map.items()}
        w.setStyleSheet(template.format(**values))

    bind_font_scale(widget, _apply)


def scaled_font_px(base: int) -> int:
    app = QApplication.instance()
    if app is None:
        return base
    return _scaled_px(base, current_font_scale(app))


def apply_theme(app: QApplication, mode: str = "light") -> None:
    app.setStyle("Fusion")
    app.setProperty("theme_mode", mode)
    scale = current_font_scale(app)
    base_font_size = _scaled_px(11, scale)
    title_font = _scaled_px(28, scale)
    subtitle_font = _scaled_px(14, scale)
    button_font = _scaled_px(14, scale)
    back_button_font = _scaled_px(20, scale)
    settings_icon_font = _scaled_px(28, scale)

    family = current_font_family(app)
    palette = QPalette()
    if mode == "dark":
        # Modo oscuro complementario (dusty rose como acento)
        bg = QColor("#1F1D22")
        base = QColor("#15131A")
        text = QColor("#F7F4F1")
        subtle = QColor("#3A3542")
        accent = QColor("#B07A8C")

        palette.setColor(QPalette.Window, bg)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Base, base)
        palette.setColor(QPalette.AlternateBase, QColor("#201E25"))
        palette.setColor(QPalette.ToolTipBase, QColor("#26232B"))
        palette.setColor(QPalette.ToolTipText, text)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, accent)
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.PlaceholderText, QColor("#8F8697"))

        app.setPalette(palette)
        app.setFont(QFont(family, base_font_size))
        app.setStyleSheet(
            f"""
            QWidget {{ background: #1F1D22; color: #F7F4F1; }}
            QMainWindow {{ background: #1F1D22; }}
            QFrame#Card {{ background: #15131A; border: 1px solid #3A3542; border-radius: 16px; }}
            QLabel#Title {{ font-size: {title_font}px; font-weight: 700; color: #F7F4F1; }}
            QLabel#Subtitle {{ font-size: {subtitle_font}px; color: #B9AFC0; }}
            QPushButton {{
                background: #B07A8C;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                min-height: 40px;
                font-size: {button_font}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #9A5D73; }}
            QPushButton:pressed {{ background: #834C63; }}
            QPushButton:disabled {{ background: #3A3542; color: #8F8697; }}
            QPushButton#BackButton {{
                min-height: 42px;
                min-width: 42px;
                max-height: 42px;
                max-width: 42px;
                border-radius: 12px;
                background: #B07A8C;
                color: #FFFFFF;
                font-size: {back_button_font}px;
                font-weight: 700;
            }}
            QPushButton#BackButton:hover {{ background: #9A5D73; }}
            QPushButton#BackButton:pressed {{ background: #834C63; }}
            QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit, QComboBox {{
                border: 1px solid #3A3542;
                border-radius: 8px;
                padding: 6px 10px;
                background: #1F1D22;
                color: #F7F4F1;
            }}
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
                border: 1px solid #B07A8C;
            }}
            QComboBox QListView {{
                background: #15131A;
                border: 1px solid #3A3542;
                selection-background-color: #B07A8C;
                selection-color: #ffffff;
            }}
            QScrollArea {{ border: none; }}
            QTextEdit {{ border: 1px solid #3A3542; border-radius: 8px; background: #1F1D22; color: #F7F4F1; }}
            QGroupBox {{ border: 1px solid #3A3542; border-radius: 10px; margin-top: 12px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #B9AFC0; }}
            QTabWidget::pane {{ border: 1px solid #3A3542; border-radius: 10px; background: #1F1D22; }}
            QFrame#NavPanel {{
                background: #201E25;
                border: 1px solid #3A3542;
                border-radius: 18px;
            }}
            QFrame#Card QLabel {{ background: transparent; }}
            QFrame#NavPanel QLabel {{ background: transparent; }}
            QFrame#TopNav {{
                background: #15131A;
                border: 1px solid #3A3542;
                border-radius: 12px;
            }}
            QFrame#TopNav QPushButton {{ min-width: 120px; }}
            QTabBar::tab {{
                background: #1F1D22;
                color: #F7F4F1;
                padding: 8px 16px;
                border: 1px solid #3A3542;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{ background: #B07A8C; color: #ffffff; }}
            QTabBar::tab:hover {{ background: #9A5D73; }}
            QToolButton#SettingsButton {{
                background: transparent;
                border: none;
                color: #F7F4F1;
                font-size: {settings_icon_font}px;
                min-width: 40px;
                min-height: 40px;
                padding: 6px;
                border-radius: 20px;
            }}
            QToolButton#SettingsButton:hover {{ color: #B07A8C; }}
            """
        )
    else:
        # Claro Ivory Chic
        bg = QColor("#FAF7F5")
        base = QColor("#FFFFFF")
        text = QColor("#4F3A47")
        accent = QColor("#B07A8C")

        palette.setColor(QPalette.Window, bg)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Base, base)
        palette.setColor(QPalette.AlternateBase, QColor("#F1E6E4"))
        palette.setColor(QPalette.ToolTipBase, QColor("#F1E6E4"))
        palette.setColor(QPalette.ToolTipText, QColor("#4F3A47"))
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, accent)
        palette.setColor(QPalette.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Highlight, accent)
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.PlaceholderText, QColor("#B09CA7"))
        app.setPalette(palette)
        app.setFont(QFont(family, base_font_size))
        app.setStyleSheet(
            f"""
            QWidget {{ background: #FAF7F5; color: #4F3A47; }}
            QMainWindow {{ background: #FAF7F5; }}
            QFrame#Card {{ background: #F1E6E4; border: 1px solid #D9C8C5; border-radius: 16px; }}
            QLabel#Title {{ font-size: {title_font}px; font-weight: 700; color: #6E4B5E; }}
            QLabel#Subtitle {{ font-size: {subtitle_font}px; color: #A78A94; }}
            QPushButton {{
                background: #B07A8C;
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                min-height: 40px;
                font-size: {button_font}px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #9A5D73; }}
            QPushButton:pressed {{ background: #834C63; }}
            QPushButton:disabled {{ background: #E5D9D7; color: #BBA9AE; }}
            QPushButton#BackButton {{
                min-height: 42px;
                min-width: 42px;
                max-height: 42px;
                max-width: 42px;
                border-radius: 12px;
                background: #B07A8C;
                color: #FFFFFF;
                font-size: {back_button_font}px;
                font-weight: 700;
            }}
            QPushButton#BackButton:hover {{ background: #9A5D73; }}
            QPushButton#BackButton:pressed {{ background: #834C63; }}
            QLineEdit, QSpinBox, QTextEdit, QPlainTextEdit, QComboBox {{
                border: 1px solid #D9C8C5;
                border-radius: 8px;
                padding: 6px 10px;
                background: #FFFFFF;
                color: #4F3A47;
            }}
            QLineEdit:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
                border: 1px solid #B07A8C;
            }}
            QComboBox QListView {{
                background: #FFFFFF;
                border: 1px solid #D9C8C5;
                selection-background-color: #B07A8C;
                selection-color: #ffffff;
            }}
            QScrollArea {{ border: none; }}
            QTextEdit {{ border: 1px solid #D9C8C5; border-radius: 8px; background: #FFFFFF; }}
            QGroupBox {{ border: 1px solid #D9C8C5; border-radius: 10px; margin-top: 12px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #A78A94; }}
            QTabWidget::pane {{ border: 1px solid #D9C8C5; border-radius: 12px; background: #FFFFFF; }}
            QTabBar::tab {{
                min-width: 120px;
                background: #F1E6E4;
                color: #6E4B5E;
                padding: 8px 16px;
                border: 1px solid #D9C8C5;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{ background: #B07A8C; color: #ffffff; }}
            QTabBar::tab:hover {{ background: #9A5D73; color: #ffffff; }}
            QFrame#NavPanel {{
                background: #F1E6E4;
                border: 1px solid #D9C8C5;
                border-radius: 18px;
            }}
            QFrame#Card QLabel {{ background: transparent; }}
            QFrame#NavPanel QLabel {{ background: transparent; }}
            QFrame#TopNav {{
                background: #F1E6E4;
                border: 1px solid #D9C8C5;
                border-radius: 12px;
            }}
            QFrame#TopNav QPushButton {{ min-width: 120px; }}
            QToolButton#SettingsButton {{
                background: transparent;
                border: none;
                color: #6E4B5E;
                font-size: {settings_icon_font}px;
                min-width: 40px;
                min-height: 40px;
                padding: 6px;
                border-radius: 20px;
            }}
            QToolButton#SettingsButton:hover {{ color: #9A5D73; }}
            """
        )
    try:
        _theme_bus.themeChanged.emit(mode)
    except Exception:
        pass


def current_mode(app: QApplication) -> str:
    return app.property("theme_mode") or "light"


def toggle_theme(app: QApplication) -> None:
    mode = current_mode(app)
    apply_theme(app, "dark" if mode == "light" else "light")


class ThemeSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("")
        self.setObjectName("ThemeSwitch")
        self.setFixedSize(120, 44)
        self._offset = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.finished.connect(self._snap_offset)

    def sizeHint(self):
        return self.size()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track_rect = QRectF(8, 10, self.width() - 16, self.height() - 20)
        radius = track_rect.height() / 2

        app = QApplication.instance()
        mode = current_mode(app)

        if mode == "dark":
            track_off = QColor("#3A3542")
            track_on = QColor("#B07A8C")
            thumb_shadow = QColor(0, 0, 0, 60)
            icon_color = QColor("#F7F4F1")
        else:
            track_off = QColor("#D9C8C5")
            track_on = QColor("#B07A8C")
            thumb_shadow = QColor(0, 0, 0, 40)
            icon_color = QColor("#6E4B5E")

        track_color = track_on if self._offset >= 0.5 else track_off

        painter.setPen(Qt.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(track_rect, radius, radius)

        # Etiqueta sobre la pista
        painter.save()
        painter.setPen(icon_color if mode == "dark" else QColor("#6E4B5E"))
        font = painter.font()
        font.setPointSize(11)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.setOpacity(0.6 if mode == "light" else 0.45)
        text_rect = QRectF(
            track_rect.left() + 10,
            track_rect.top(),
            track_rect.width() - 20,
            track_rect.height(),
        )
        painter.drawText(text_rect, Qt.AlignCenter, "Tema")
        painter.restore()

        # Knob
        knob_d = track_rect.height() - 6
        x = track_rect.left() + 3 + (track_rect.width() - knob_d) * self._offset
        knob_rect = QRectF(x, track_rect.top() + 3, knob_d, knob_d)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.setPen(QPen(thumb_shadow, 1))
        painter.drawEllipse(knob_rect)

    def nextCheckState(self):
        start = self._offset
        end = 0.0 if self.isChecked() else 1.0
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
        super().nextCheckState()

    def _snap_offset(self):
        self.setOffset(1.0 if self.isChecked() else 0.0)

    def getOffset(self) -> float:
        return self._offset

    def setOffset(self, value: float) -> None:
        self._offset = max(0.0, min(1.0, float(value)))
        self.update()

    offset = Property(float, getOffset, setOffset)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.setOffset(1.0 if checked else 0.0)

def make_theme_toggle_button(parent_widget) -> QCheckBox:
    """Crea un switch que alterna claro/oscuro y actualiza su estado."""
    app = QApplication.instance()
    switch = ThemeSwitch(parent_widget)
    switch.setToolTip("Alternar entre modo claro y modo oscuro")
    switch.setChecked(current_mode(app) == "dark")

    def _sync_state():
        switch.blockSignals(True)
        desired = current_mode(app) == "dark"
        if switch.isChecked() != desired:
            switch.setChecked(desired)
        elif switch._anim.state() != QAbstractAnimation.Running:
            switch.setOffset(1.0 if desired else 0.0)
        switch.blockSignals(False)

    def _toggle():
        toggle_theme(app)
        _sync_state()

    switch.toggled.connect(lambda _checked: _toggle())
    def _on_theme_changed(_mode):
        _sync_state()

    theme_changed_signal().connect(_on_theme_changed)

    def _cleanup(*_args):
        try:
            theme_changed_signal().disconnect(_on_theme_changed)
        except Exception:
            pass

    switch.destroyed.connect(_cleanup)
    _sync_state()
    return switch


def install_toggle_shortcut(window) -> None:
    """Instala Ctrl+D para alternar tema en la ventana dada."""
    app = QApplication.instance()
    sc = QShortcut(QKeySequence("Ctrl+D"), window)

    def _activate():
        toggle_theme(app)
        for sw in window.findChildren(ThemeSwitch):
            sw.blockSignals(True)
            sw.setChecked(current_mode(app) == "dark")
            sw.blockSignals(False)

    sc.activated.connect(_activate)
