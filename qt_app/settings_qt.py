from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor

from .theme import (
    current_font_scale,
    set_font_scale,
    current_font_family,
    set_font_family,
    current_mode,
    apply_theme,
)


_FONT_SIZE_OPTIONS = [
    ("Letra compacta", 0.9),
    ("Letra estandar", 1.0),
    ("Letra grande", 1.2),
    ("Letra extra grande", 1.35),
    ("Letra maxima", 1.5),
]

_FONT_FAMILY_OPTIONS = [
    "Segoe UI",
    "Calibri",
    "Arial",
    "Verdana",
    "Tahoma",
    "Times New Roman",
    "Consolas",
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuracion de interfaz")
        self.setModal(True)
        # Icono de ventana: engranaje sin fondo
        try:
            pm = QPixmap(64, 64)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing)
            color = self.palette().windowText().color() if self.palette() else QColor("#444")
            p.setPen(Qt.NoPen)
            p.setBrush(Qt.NoBrush)
            p.setPen(color)
            f = QFont()
            f.setPointSize(40)
            f.setBold(True)
            p.setFont(f)
            p.drawText(pm.rect(), Qt.AlignCenter, "⚙")
            p.end()
            self.setWindowIcon(QIcon(pm))
        except Exception:
            pass

        layout = QVBoxLayout(self)

        # Encabezado con icono de engranaje (sin fondo)
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        gear = QLabel("⚙")
        gear.setAlignment(Qt.AlignCenter)
        gear.setStyleSheet("font-size: 24px; background: transparent;")
        header_row.addWidget(gear, 0, Qt.AlignVCenter)

        title_box = QVBoxLayout()
        title = QLabel("Configuracion de interfaz")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-weight:700; font-size:18px;")
        subtitle = QLabel("Personaliza la apariencia de la calculadora")
        subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subtitle.setStyleSheet("color: #6b7280;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_row.addLayout(title_box, 1)

        layout.addLayout(header_row)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        layout.addLayout(form)

        # Tema claro/oscuro
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Tema claro", "light")
        self.theme_combo.addItem("Tema oscuro", "dark")
        current_theme = current_mode(self._app())
        idx_theme = max(0, self.theme_combo.findData(current_theme))
        self.theme_combo.setCurrentIndex(idx_theme)
        form.addRow("Tema:", self.theme_combo)

        # Tamano de fuente
        self.font_scale_combo = QComboBox()
        for label, value in _FONT_SIZE_OPTIONS:
            self.font_scale_combo.addItem(label, value)
        current_scale = current_font_scale(self._app())
        idx_scale = min(
            range(self.font_scale_combo.count()),
            key=lambda i: abs(self.font_scale_combo.itemData(i) - current_scale),
        )
        self.font_scale_combo.setCurrentIndex(idx_scale)
        form.addRow("Tamano de letra:", self.font_scale_combo)

        # Familia tipografica
        self.font_family_combo = QComboBox()
        self.font_family_combo.setEditable(True)
        for family in _FONT_FAMILY_OPTIONS:
            if self.font_family_combo.findText(family, Qt.MatchFixedString) == -1:
                self.font_family_combo.addItem(family)
        current_family = current_font_family(self._app())
        if self.font_family_combo.findText(current_family, Qt.MatchFixedString) == -1:
            self.font_family_combo.addItem(current_family)
        self.font_family_combo.setCurrentText(current_family)
        form.addRow("Tipo de letra:", self.font_family_combo)

        info = QLabel(
            "Los cambios se aplican inmediatamente y se recuerdan para futuras sesiones."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignLeft)
        info.setStyleSheet("color: #6b7280;")
        layout.addWidget(info)

        # Botonera minimalista: solo "Cerrar". Los cambios se aplican al instante.
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Aplicar cambios automaticamente cuando el usuario modifica opciones
        self.theme_combo.currentIndexChanged.connect(self.apply_changes)
        self.font_scale_combo.currentIndexChanged.connect(self.apply_changes)
        try:
            self.font_family_combo.currentTextChanged.connect(self.apply_changes)
        except Exception:
            # Compatibilidad segun versiones de Qt
            self.font_family_combo.editTextChanged.connect(self.apply_changes)

    def _app(self):
        from PySide6.QtWidgets import QApplication

        return QApplication.instance()

    def apply_changes(self):
        app = self._app()
        changed = False

        # Fuente (familia)
        chosen_family = self.font_family_combo.currentText().strip()
        if chosen_family and chosen_family != current_font_family(app):
            set_font_family(app, chosen_family)
            changed = True

        # Escala de fuente
        chosen_scale = float(self.font_scale_combo.currentData())
        if abs(chosen_scale - current_font_scale(app)) > 1e-6:
            set_font_scale(app, chosen_scale)
            changed = True

        # Tema
        chosen_theme = self.theme_combo.currentData()
        if chosen_theme != current_mode(app):
            apply_theme(app, chosen_theme)
            changed = True

        if changed:
            # actualizar familia mostrada despues de aplicar (por si se normalizo)
            self.font_family_combo.setCurrentText(current_font_family(app))

    def accept(self):
        self.apply_changes()
        super().accept()


def open_settings_dialog(parent=None):
    dlg = SettingsDialog(parent)
    dlg.exec()
