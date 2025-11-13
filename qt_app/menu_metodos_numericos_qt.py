from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QToolButton,
    QMenu,
)
from PySide6.QtCore import Qt, QSize
from .theme import install_toggle_shortcut, bind_theme_icon, make_overflow_icon, gear_icon_preferred
from .settings_qt import open_settings_dialog
from .metodos.biseccion_qt import MetodoBiseccionWindow
from .metodos.falsa_posicion_qt import MetodoFalsaPosicionWindow
from .metodos.newton_raphson_qt import MetodoNewtonRaphsonWindow


class MenuMetodosNumericosWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Métodos Numéricos")

        container = QWidget()
        self.setCentralWidget(container)
        outer = QVBoxLayout(container)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        top_bar = QFrame()
        top_bar.setObjectName("TopNav")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        top_layout.setSpacing(12)

        btn_back = QPushButton("\u2190")
        btn_back.setObjectName("BackButton")
        btn_back.setIconSize(QSize(24, 24))
        btn_back.setFixedSize(42, 42)
        btn_back.setToolTip("Volver")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)

        top_layout.addSpacing(6)

        btn_biseccion = QPushButton("Método de Bisección")
        btn_biseccion.setMinimumHeight(36)
        btn_biseccion.clicked.connect(self._open_biseccion)
        top_layout.addWidget(btn_biseccion)

        btn_falsa_pos = QPushButton("Método de Falsa Posición")
        btn_falsa_pos.setMinimumHeight(36)
        btn_falsa_pos.clicked.connect(self._open_falsa_posicion)
        top_layout.addWidget(btn_falsa_pos)

        btn_newton = QPushButton("Método de Newton-Raphson")
        btn_newton.setMinimumHeight(36)
        btn_newton.clicked.connect(self._open_newton_raphson)
        top_layout.addWidget(btn_newton)

        top_layout.addStretch(1)

        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("Más opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        # sin tamaño fijo
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuración")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top_layout.addWidget(more_btn, 0, Qt.AlignVCenter)

        outer.addWidget(top_bar)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        title = QLabel("Métodos Numéricos")
        title.setObjectName("Title")
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Centraliza técnicas de análisis numérico para aproximar raíces y resolver problemas complejos "
            "de forma guiada. Selecciona un método desde la barra superior para comenzar."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(12)

        details = QLabel(
            "Disponible ahora:\n"
            "- Método de Bisección con reporte paso a paso, resumen destacado y validaciones del intervalo.\n"
            "- Método de Falsa Posición heredado del flujo de bisección con reportes completos.\n"
            "- Método de Newton-Raphson con derivada numérica y seguimiento de cada iteración.\n"
            "\nEn desarrollo:\n"
            "- Nuevos métodos de aproximación con interfaces interactivas.\n"
            "- Integración con historiales para comparar iteraciones clave."
        )
        details.setWordWrap(True)
        card_layout.addWidget(details)

        card_layout.addStretch(1)
        outer.addWidget(card, 1)

        install_toggle_shortcut(self)

    def _go_back(self):
        try:
            parent = self.parent()
            self.close()
            if parent is not None:
                parent.show()
                parent.activateWindow()
        except Exception:
            self.close()

    def _open_biseccion(self):
        w = MetodoBiseccionWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_falsa_posicion(self):
        w = MetodoFalsaPosicionWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_newton_raphson(self):
        w = MetodoNewtonRaphsonWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_settings(self):
        open_settings_dialog(self)
