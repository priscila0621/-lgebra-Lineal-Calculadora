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
from .metodos.secante_qt import MetodoSecanteWindow


class MenuMetodosNumericosWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metodos Numericos")

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

        btn_biseccion = QPushButton("Metodo de Biseccion")
        btn_biseccion.setMinimumHeight(36)
        btn_biseccion.clicked.connect(self._open_biseccion)
        top_layout.addWidget(btn_biseccion)

        btn_falsa_pos = QPushButton("Metodo de Falsa Posicion")
        btn_falsa_pos.setMinimumHeight(36)
        btn_falsa_pos.clicked.connect(self._open_falsa_posicion)
        top_layout.addWidget(btn_falsa_pos)

        btn_newton = QPushButton("Metodo de Newton-Raphson")
        btn_newton.setMinimumHeight(36)
        btn_newton.clicked.connect(self._open_newton_raphson)
        top_layout.addWidget(btn_newton)

        btn_secante = QPushButton("Metodo de la secante")
        btn_secante.setMinimumHeight(36)
        btn_secante.clicked.connect(self._open_secante)
        top_layout.addWidget(btn_secante)

        top_layout.addStretch(1)

        more_btn = QToolButton()
        more_btn.setAutoRaise(True)
        more_btn.setCursor(Qt.PointingHandCursor)
        more_btn.setToolTip("Mas opciones")
        more_btn.setPopupMode(QToolButton.InstantPopup)
        try:
            bind_theme_icon(more_btn, make_overflow_icon, 20)
            more_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
        menu = QMenu(more_btn)
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuracion")
        act_settings.triggered.connect(self._open_settings)
        more_btn.setMenu(menu)
        top_layout.addWidget(more_btn, 0, Qt.AlignVCenter)

        outer.addWidget(top_bar)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        title = QLabel("Metodos Numericos")
        title.setObjectName("Title")
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Centraliza tecnicas de analisis numerico para aproximar raices y resolver problemas complejos "
            "de forma guiada. Selecciona un metodo desde la barra superior para comenzar."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(12)

        details = QLabel(
            "Disponible ahora:\n"
            "- Metodo de Biseccion con reporte paso a paso, resumen destacado y validaciones del intervalo.\n"
            "- Metodo de Falsa Posicion heredado del flujo de biseccion con reportes completos.\n"
            "- Metodo de Newton-Raphson con derivada numerica y seguimiento de cada iteracion.\n"
            "- Metodo de la secante con dos aproximaciones iniciales y tabla de iteraciones completa.\n"
            "\nEn desarrollo:\n"
            "- Nuevos metodos de aproximacion con interfaces interactivas.\n"
            "- Integracion con historiales para comparar iteraciones clave."
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

    def _open_secante(self):
        w = MetodoSecanteWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_settings(self):
        open_settings_dialog(self)
