from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QMenu,
    QToolButton,
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os

from .menu_principal_qt import MenuPrincipalWindow
from .menu_principal_numerico_qt import MenuNumericoPrincipalWindow
from .theme import (
    install_toggle_shortcut,
    bind_font_scale_stylesheet,
    make_gear_icon,
    bind_theme_icon,
    gear_icon_preferred,
    make_overflow_icon,
)
from .settings_qt import open_settings_dialog


class SelectorInicioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seleccionar módulo")

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        # Barra superior con menú de tres puntos (esquina superior derecha)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.addStretch(1)
        btn_more = QToolButton()
        btn_more.setText("")
        btn_more.setAutoRaise(True)
        btn_more.setCursor(Qt.PointingHandCursor)
        btn_more.setToolTip("Más opciones")
        btn_more.setPopupMode(QToolButton.InstantPopup)
        try:
            from PySide6.QtCore import QSize
            bind_theme_icon(btn_more, make_overflow_icon, 20)
            btn_more.setIconSize(QSize(20, 20))
        except Exception:
            pass
        # sin tamaño fijo
        menu = QMenu(btn_more)
        act_settings = menu.addAction(gear_icon_preferred(22), "Configuración")
        act_settings.triggered.connect(self._open_settings)
        btn_more.setMenu(menu)
        top_bar.addWidget(btn_more, 0, Qt.AlignRight)
        outer.addLayout(top_bar)

        # Presentación (logo + nombre + descripción)
        hero = QHBoxLayout()
        hero.setSpacing(16)

        logo = QLabel("NL")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(84, 84)
        bind_font_scale_stylesheet(
            logo,
            """
            QLabel {{
                background-color: #B07A8C;
                color: #FFFFFF;
                border-radius: 42px;
                font-size: {logo}px;
                font-weight: 700;
                letter-spacing: 3px;
            }}
            """,
            logo=28,
        )
        hero.addWidget(logo, 0, Qt.AlignTop)

        head_box = QVBoxLayout()
        title = QLabel("Nexus Linear — Calculadora Inteligente")
        title.setObjectName("Title")
        head_box.addWidget(title)

        subtitle = QLabel(
            "Suite para álgebra lineal y métodos numéricos. "
            "Explora módulos especializados con resultados claros."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        head_box.addWidget(subtitle)
        hero.addLayout(head_box, 1)

        outer.addLayout(hero)

        # (menú ya agregado en la parte superior)

        # Tarjetas centradas
        cards = QHBoxLayout()
        cards.setSpacing(36)

        cards.addWidget(
            self._build_card(
                title="Álgebra Lineal",
                img_relpath=self._project_path("assets/selector/algebra.png"),
                on_click=self._open_algebra,
            ),
            0,
        )

        cards.addWidget(
            self._build_card(
                title="Métodos Numéricos",
                img_relpath=self._project_path("assets/selector/analisis.png"),
                on_click=self._open_numerico,
            ),
            0,
        )

        # Centrado horizontal y un poco más abajo en altura
        outer.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addLayout(cards)
        row.addStretch(1)
        outer.addLayout(row)

        outer.addStretch(1)

        # Nota: omitimos créditos en esta vista inicial para evitar recortes

        install_toggle_shortcut(self)

    def _open_settings(self):
        open_settings_dialog(self)

    def _build_card(self, title: str, img_relpath: str, on_click):
        card = QFrame()
        card.setObjectName("OptionCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)
        card.setMaximumWidth(360)
        card.setMinimumWidth(260)
        # Estilo: mismo borde por todos lados y panel blanco para la imagen
        card.setStyleSheet(
            "#OptionCard { background: #f3e6e9; border-radius: 16px; }"
        )

        # Panel blanco interno
        img_panel = QFrame()
        img_panel.setObjectName("ImgPanel")
        img_panel.setStyleSheet(
            "#ImgPanel { background: #ffffff; border: 1px solid #e2d5db; border-radius: 12px; }"
        )
        img_panel_lay = QVBoxLayout(img_panel)
        img_panel_lay.setContentsMargins(16, 16, 16, 16)
        img_panel_lay.setSpacing(0)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        abs_path = img_relpath
        if abs_path and os.path.exists(abs_path):
            pm = QPixmap(abs_path)
            if not pm.isNull():
                img_label.setPixmap(pm.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText("Sin imagen")
            img_label.setAlignment(Qt.AlignCenter)
        img_panel_lay.addWidget(img_label)
        lay.addWidget(img_panel)

        btn = QPushButton(title)
        btn.setMinimumHeight(40)
        btn.clicked.connect(on_click)
        lay.addWidget(btn)

        return card

    def _project_path(self, relpath: str) -> str:
        """Devuelve ruta absoluta relativa a la raíz del proyecto."""
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            root = os.path.abspath(os.path.join(here, os.pardir))
            return os.path.join(root, relpath.replace("/", os.sep))
        except Exception:
            return relpath

    def _restore_focus(self):
        self._child = None
        self.show()
        try:
            self.activateWindow()
            self.raise_()
        except Exception:
            pass

    def _open_algebra(self):
        w = MenuPrincipalWindow(module="algebra", on_exit=self._restore_focus)
        w.setAttribute(Qt.WA_DeleteOnClose, True)
        w.showMaximized()
        self._child = w
        self.hide()

    def _open_numerico(self):
        w = MenuNumericoPrincipalWindow(on_exit=self._restore_focus)
        w.setAttribute(Qt.WA_DeleteOnClose, True)
        w.showMaximized()
        self._child = w
        self.hide()



