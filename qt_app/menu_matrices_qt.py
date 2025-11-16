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


class MenuMatricesWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Operaciones con Matrices")

        outer = QWidget()
        self.setCentralWidget(outer)
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(24, 24, 24, 24)
        outer_lay.setSpacing(18)

        # Barra superior con subopciones
        nav = QFrame()
        nav.setObjectName("TopNav")
        nav_lay = QHBoxLayout(nav)
        nav_lay.setContentsMargins(18, 12, 18, 12)
        nav_lay.setSpacing(12)

        btn_back = QPushButton("\u2190")
        btn_back.setObjectName("BackButton")
        btn_back.setIconSize(QSize(24, 24))
        btn_back.setFixedSize(42, 42)
        btn_back.setToolTip("Volver")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._go_back)
        nav_lay.addWidget(btn_back)

        nav_lay.addSpacing(6)

        btn_suma = QPushButton("Suma")
        btn_suma.setMinimumHeight(36)
        btn_suma.clicked.connect(self._open_suma)
        nav_lay.addWidget(btn_suma)

        btn_resta = QPushButton("Resta")
        btn_resta.setMinimumHeight(36)
        btn_resta.clicked.connect(self._open_resta)
        nav_lay.addWidget(btn_resta)

        btn_mult = QPushButton("Multiplicación")
        btn_mult.setMinimumHeight(36)
        btn_mult.clicked.connect(self._open_mult)
        nav_lay.addWidget(btn_mult)

        btn_det = QPushButton("Determinante")
        btn_det.setMinimumHeight(36)
        btn_det.clicked.connect(self._open_det)
        nav_lay.addWidget(btn_det)

        btn_trans = QPushButton("Transpuesta")
        btn_trans.setMinimumHeight(36)
        btn_trans.clicked.connect(self._open_trans)
        nav_lay.addWidget(btn_trans)

        btn_inv = QPushButton("Inversa")
        btn_inv.setMinimumHeight(36)
        btn_inv.clicked.connect(self._open_inv)
        nav_lay.addWidget(btn_inv)

        nav_lay.addStretch(1)
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
        nav_lay.addWidget(more_btn, 0, Qt.AlignRight)
        outer_lay.addWidget(nav)

        # Contenido informativo
        card = QFrame()
        card.setObjectName("Card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(32, 28, 32, 28)
        card_lay.setSpacing(16)

        title = QLabel("Operaciones con Matrices")
        title.setObjectName("Title")
        card_lay.addWidget(title)

        subtitle = QLabel(
            "Utiliza la barra de navegación superior para abrir la herramienta que necesites. "
            "Cada módulo permite ingresar matrices de forma guiada, aplicar escalares y obtener reportes detallados."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        card_lay.addWidget(subtitle)

        card_lay.addSpacing(12)

        details = QLabel(
            "Consejo profesional:\n"
            "• Suma y resta aceptan múltiples matrices con seguimiento paso a paso.\n"
            "• Multiplicación incorpora escalado y cadena de operaciones.\n"
            "• Determinante, transpuesta e inversa generan visualizaciones claras listas para compartir."
        )
        details.setWordWrap(True)
        card_lay.addWidget(details)

        card_lay.addStretch(1)
        outer_lay.addWidget(card, 1)

        install_toggle_shortcut(self)

    def _go_back(self):
        try:
            p = self.parent()
            self.close()
            if p is not None:
                p.show()
                p.activateWindow()
        except Exception:
            self.close()

    def _open_suma(self):
        from .matrices_qt import SumaMatricesWindow
        w = SumaMatricesWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_resta(self):
        from .matrices_qt import RestaMatricesWindow
        w = RestaMatricesWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_mult(self):
        from .matrices_qt import MultiplicacionMatricesWindow
        w = MultiplicacionMatricesWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_det(self):
        from .matrices_qt import DeterminanteMatrizWindow
        w = DeterminanteMatrizWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_trans(self):
        from .matrices_qt import TranspuestaMatrizWindow
        w = TranspuestaMatrizWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_inv(self):
        from .matrices_qt import InversaMatrizWindow
        w = InversaMatrizWindow(parent=self)
        w.showMaximized()
        self._child = w

    def _open_settings(self):
        open_settings_dialog(self)

