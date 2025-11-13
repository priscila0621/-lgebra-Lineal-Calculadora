from typing import Callable, Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QSizePolicy,
    QToolButton,
    QMenu,
)
from PySide6.QtCore import Qt, QSize
from .menu_matrices_qt import MenuMatricesWindow
from .menu_sistemas_qt import MenuSistemasWindow
from .independencia_qt import IndependenciaWindow
from .transformaciones_qt import TransformacionesWindow
from .menu_metodos_numericos_qt import MenuMetodosNumericosWindow
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


class MenuPrincipalWindow(QMainWindow):
    def __init__(self, module: str = "algebra", parent=None, on_exit: Optional[Callable[[], None]] = None):
        super().__init__(parent)
        self._on_exit = on_exit
        self._exit_notified = False
        # Contexto del módulo seleccionado ("algebra" o "all").
        # Por defecto mostramos solo las opciones de Álgebra Lineal.
        self.module = (module or "algebra").lower()
        self.setWindowTitle("Calculadora Álgebra Lineal")

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
        # sin tamaño fijo; dejamos que el layout ajuste
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

        # Navegación lateral
        nav = QFrame()
        nav.setObjectName("NavPanel")
        nav.setFixedWidth(260)
        nav_lay = QVBoxLayout(nav)
        nav_lay.setContentsMargins(24, 24, 24, 24)
        nav_lay.setSpacing(18)

        # Botón volver discreto en el panel lateral
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

        nav_title = QLabel("Menú principal" if self.module != "algebra" else "Álgebra Lineal")
        nav_title.setObjectName("Title")
        nav_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        nav_lay.addWidget(nav_title)

        nav_sub = QLabel(
            "Explora cada módulo especializado."
            if self.module != "algebra"
            else "Explora los módulos de álgebra lineal."
        )
        nav_sub.setObjectName("Subtitle")
        nav_sub.setWordWrap(True)
        nav_lay.addWidget(nav_sub)

        self.btn_sistemas = QPushButton("Sistemas de ecuaciones")
        self.btn_sistemas.setMinimumHeight(44)
        self.btn_sistemas.clicked.connect(self._open_sistemas)
        nav_lay.addWidget(self.btn_sistemas)

        self.btn_matrices = QPushButton("Operaciones con matrices")
        self.btn_matrices.setMinimumHeight(44)
        self.btn_matrices.clicked.connect(self._open_matrices)
        nav_lay.addWidget(self.btn_matrices)

        self.btn_independencia = QPushButton("Independencia de vectores")
        self.btn_independencia.setMinimumHeight(44)
        self.btn_independencia.clicked.connect(self._open_independencia)
        nav_lay.addWidget(self.btn_independencia)

        self.btn_transformaciones = QPushButton("Transformaciones lineales")
        self.btn_transformaciones.setMinimumHeight(44)
        self.btn_transformaciones.clicked.connect(self._open_transformaciones)
        nav_lay.addWidget(self.btn_transformaciones)

        self.btn_metodos = QPushButton("Métodos numéricos")
        self.btn_metodos.setMinimumHeight(44)
        self.btn_metodos.clicked.connect(self._open_metodos_numericos)
        # Mostrar solo si el contexto no es exclusivamente algebra
        if self.module != "algebra":
            nav_lay.addWidget(self.btn_metodos)

        nav_lay.addStretch(1)

        # (Se movió la configuración al menú de tres puntos en la esquina superior derecha)

        about = QLabel(
            "\u00A9 2025 - Priscila Selva - Emma Serrano - Jeyni Orozco\n"
            "Todos los derechos reservados."
        )
        about.setWordWrap(True)
        about.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        about.setObjectName("Subtitle")
        nav_lay.addWidget(about)

        base.addWidget(nav)

        # Panel principal con informacion
        content = QFrame()
        content.setObjectName("Card")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(32, 32, 32, 32)
        content_lay.setSpacing(20)

        # (Top bar de contenido no necesario; el menú global ya ocupa la esquina superior derecha)

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
        heading = QLabel(
            "Nexus Linear - Calculadora Inteligente"
            if self.module != "algebra"
            else "Nexus Linear - Álgebra Lineal"
        )
        heading.setObjectName("Title")
        title_box.addWidget(heading)

        strapline = QLabel(
            (
                "Una suite profesional para explorar, resolver y visualizar problemas de álgebra lineal. "
                "Integramos herramientas interactivas para docentes, estudiantes y profesionales."
            )
            if self.module == "algebra"
            else (
                "Una suite profesional para álgebra lineal y métodos numéricos. "
                "Integramos herramientas interactivas con resultados claros."
            )
        )
        strapline.setObjectName("Subtitle")
        strapline.setWordWrap(True)
        title_box.addWidget(strapline)

        title_box.addSpacing(8)

        highlights = QLabel(
            "\u2022 Automatiza cálculos complejos con precisión fraccional.\n"
            "\u2022 Documenta cada procedimiento con trazabilidad paso a paso.\n"
            "\u2022 Diseñada para la Universidad de Tecnología: innovación aplicada."
        )
        highlights.setWordWrap(True)
        highlights.setAlignment(Qt.AlignLeft)
        title_box.addWidget(highlights)

        hero.addLayout(title_box, 1)
        content_lay.addLayout(hero)

        content_lay.addSpacing(12)

        info_title = QLabel(
            "Acerca de la plataforma" if self.module != "algebra" else "Acerca de Álgebra Lineal"
        )
        info_title.setObjectName("Subtitle")
        info_title.setStyleSheet("text-decoration: none;")
        content_lay.addWidget(info_title)

        info_body = QLabel(
            (
                "Nexus Linear centraliza las operaciones más demandadas en álgebra lineal. "
                "Desde la resolución de sistemas y la manipulación de matrices hasta el análisis de transformaciones, "
                "cada módulo ofrece una experiencia guiada con resultados instantáneos y explicación pedagógica."
            )
            if self.module == "algebra"
            else (
                "Nexus Linear integra módulos de álgebra lineal y métodos numéricos con una experiencia unificada. "
                "Selecciona un módulo para comenzar."
            )
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

    def _open_sistemas(self):
        self.s = MenuSistemasWindow(parent=self)
        self.s.showMaximized()

    def _open_matrices(self):
        self.m = MenuMatricesWindow(parent=self)
        self.m.showMaximized()

    def _open_independencia(self):
        self.w = IndependenciaWindow(parent=self)
        self.w.showMaximized()

    def _open_transformaciones(self):
        self.w = TransformacionesWindow(parent=self)
        self.w.showMaximized()

    def _open_metodos_numericos(self):
        self.w = MenuMetodosNumericosWindow(parent=self)
        self.w.showMaximized()

    def _open_settings(self):
        open_settings_dialog(self)

    def _go_back(self):
        self.close()
