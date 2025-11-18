from typing import Callable, Optional

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
from .theme import (
    install_toggle_shortcut,
    bind_font_scale_stylesheet,
    make_back_icon,
    make_gear_icon,
    make_overflow_icon,
    bind_theme_icon,
    gear_icon_preferred,
    back_icon_preferred,
)
from .settings_qt import open_settings_dialog
from .metodos.biseccion_qt import MetodoBiseccionWindow
from .metodos.falsa_posicion_qt import MetodoFalsaPosicionWindow
from .metodos.newton_raphson_qt import MetodoNewtonRaphsonWindow
from .metodos.secante_qt import MetodoSecanteWindow


class MenuNumericoPrincipalWindow(QMainWindow):
    def __init__(self, parent=None, on_exit: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self._on_exit = on_exit
        self._exit_notified = False
        self.setWindowTitle("Análisis numérico")

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(0)

        # Barra superior global con menú de tres puntos en la esquina superior derecha
        global_top = QHBoxLayout()
        global_top.setContentsMargins(0, 0, 0, 0)
        global_top.addStretch(1)
        more_btn_global = QToolButton()
        more_btn_global.setAutoRaise(True)
        more_btn_global.setCursor(Qt.PointingHandCursor)
        more_btn_global.setToolTip("Más opciones")
        more_btn_global.setPopupMode(QToolButton.InstantPopup)
        more_btn_global.setText("")
        try:
            bind_theme_icon(more_btn_global, make_overflow_icon, 20)
            more_btn_global.setIconSize(QSize(20, 20))
        except Exception:
            pass
        # sin tamaño fijo
        gmenu = QMenu(more_btn_global)
        gact_settings = gmenu.addAction(gear_icon_preferred(22), "Configuración")
        gact_settings.triggered.connect(self._open_settings)
        more_btn_global.setMenu(gmenu)
        global_top.addWidget(more_btn_global)
        outer.addLayout(global_top)

        base_container = QWidget()
        base = QHBoxLayout(base_container)
        base.setContentsMargins(24, 24, 24, 24)
        base.setSpacing(24)
        outer.addWidget(base_container, 1)

        # Navegacion lateral
        nav = QFrame()
        nav.setObjectName("NavPanel")
        nav.setFixedWidth(260)
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(24, 24, 24, 24)
        nav_lay.setSpacing(18)

        # Botón volver discreto al inicio del panel lateral
        back_btn = QToolButton()
        back_btn.setObjectName("BackButton")
        back_btn.setText("")
        back_btn.setToolTip("Volver")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setAutoRaise(True)
        back_btn.setFixedSize(44, 44)
        back_btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        try:
            bind_theme_icon(back_btn, back_icon_preferred, 24)
            back_btn.setIconSize(QSize(24, 24))
        except Exception:
            back_btn.setText("←")
        back_btn.clicked.connect(self._go_back)
        nav_lay.addWidget(back_btn, 0, Qt.AlignLeft)

        # Forzar salto de linea para que no se corte el título
        nav_title = QLabel("Análisis\nnumérico")
        nav_title.setObjectName("Title")
        nav_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        nav_title.setWordWrap(True)
        nav_lay.addWidget(nav_title)

        nav_sub = QLabel("Módulos disponibles para métodos numéricos.")
        nav_sub.setObjectName("Subtitle")
        nav_sub.setWordWrap(True)
        nav_lay.addWidget(nav_sub)

        # Módulos disponibles
        self.btn_biseccion = QPushButton("Método de bisección")
        self.btn_biseccion.setMinimumHeight(44)
        self.btn_biseccion.clicked.connect(self._open_biseccion)
        nav_lay.addWidget(self.btn_biseccion)

        self.btn_falsa_pos = QPushButton("Método de falsa posición")
        self.btn_falsa_pos.setMinimumHeight(44)
        self.btn_falsa_pos.clicked.connect(self._open_falsa_posicion)
        nav_lay.addWidget(self.btn_falsa_pos)

        self.btn_newton = QPushButton("Método de Newton-Raphson")
        self.btn_newton.setMinimumHeight(44)
        self.btn_newton.clicked.connect(self._open_newton_raphson)
        nav_lay.addWidget(self.btn_newton)
        self.btn_secante = QPushButton("Método de la secante")
        self.btn_secante.setMinimumHeight(44)
        self.btn_secante.clicked.connect(self._open_secante)
        nav_lay.addWidget(self.btn_secante)
        

        nav_lay.addStretch(1)

        # (La configuración se movió al menú de tres puntos en la esquina superior derecha)

        about = QLabel(
            "\u00A9 2025 - Priscila Selva - Emma Serrano - Jeyni Orozco\n"
            "Todos los derechos reservados."
        )
        about.setWordWrap(True)
        about.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        about.setObjectName("Subtitle")
        nav_lay.addWidget(about)

        base.addWidget(nav)

        # Panel principal con información
        content = QFrame()
        content.setObjectName("Card")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(32, 32, 32, 32)
        content_lay.setSpacing(20)

        # (El menú global ya ocupa la esquina superior derecha)

        hero = QHBoxLayout()
        hero.setSpacing(24)

        logo = QLabel("NL")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(96, 96)
        bind_font_scale_stylesheet(
            logo,
            """
            QLabel {{
                background-color: #B07A8C;
                color: #FFFFFF;
                border-radius: 48px;
                font-size: {logo}px;
                font-weight: 700;
                letter-spacing: 4px;
            }}
            """,
            logo=36,
        )
        hero.addWidget(logo, 0, Qt.AlignTop)

        title_box = QVBoxLayout()
        heading = QLabel("Nexus Linear - Análisis numérico")
        heading.setObjectName("Title")
        title_box.addWidget(heading)

        strapline = QLabel(
            "Herramientas de analisis numerico con enfoque practico. "
            "Explora biseccion, falsa posicion, secante y Newton-Raphson desde una sola vista."
        )
        strapline.setObjectName("Subtitle")
        strapline.setWordWrap(True)
        title_box.addWidget(strapline)

        title_box.addSpacing(8)

        details = QLabel(
            "Disponible ahora:\n"
            "- Metodo de biseccion con validacion del intervalo y reporte paso a paso.\n"
            "- Metodo de falsa posicion con el mismo flujo guiado, ideal para intervalos dinamicos.\n"
            "- Metodo de Newton-Raphson con derivada numerica y seguimiento iterativo detallado.\n"
            "- Metodo de la secante con dos valores iniciales, sin requerir cambio de signo."
        )
        details.setWordWrap(True)
        details.setAlignment(Qt.AlignLeft)
        title_box.addWidget(details)

        hero.addLayout(title_box, 1)
        content_lay.addLayout(hero)

        content_lay.addSpacing(12)

        info_title = QLabel("Acerca del módulo")
        info_title.setObjectName("Subtitle")
        info_title.setStyleSheet("text-decoration: none;")
        content_lay.addWidget(info_title)

        info_body = QLabel(
            "Este módulo reúne técnicas de análisis numérico orientadas a la docencia y práctica profesional. "
            "A medida que integremos nuevos métodos, aparecerán en la navegación lateral."
        )
        info_body.setWordWrap(True)
        info_body.setStyleSheet("text-decoration: none;")
        content_lay.addWidget(info_body)

        content_lay.addStretch(1)
        base.addWidget(content, 1)

        install_toggle_shortcut(self)

    def _notify_exit(self):
        if self._exit_notified:
            return
        self._exit_notified = True
        if callable(self._on_exit):
            try:
                self._on_exit()
            except Exception:
                pass
        else:
            parent = self.parent()
            if parent is not None:
                parent.show()
                parent.activateWindow()

    def closeEvent(self, event):
        self._notify_exit()
        super().closeEvent(event)

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

    def _go_back(self):
        self.close()
