from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, QSize
from .theme import install_toggle_shortcut
from .settings_qt import open_settings_dialog
from .metodos.biseccion_qt import MetodoBiseccionWindow


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

        top_layout.addStretch(1)

        btn_settings = QPushButton("Configuracion")
        btn_settings.clicked.connect(self._open_settings)
        top_layout.addWidget(btn_settings, 0, Qt.AlignVCenter)

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

    def _open_settings(self):
        open_settings_dialog(self)
