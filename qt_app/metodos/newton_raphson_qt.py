import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMessageBox,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QHeaderView,
)

from . import biseccion_qt as bq


@dataclass
class NewtonRaphsonStep:
    iteration: int
    x: float
    fx: float
    dfx: float
    x_next: float
    error: float

    @property
    def a(self) -> float:
        return self.x

    @property
    def b(self) -> float:
        return self.x_next

    @property
    def c(self) -> float:
        return self.x_next

    @property
    def fa(self) -> float:
        return self.fx

    @property
    def fb(self) -> float:
        return self.fx

    @property
    def fc(self) -> float:
        return self.fx


def _numeric_derivative(func: Callable[[float], float], x: float, h: float = 1e-6) -> float:
    fx_forward = func(x + h)
    fx_backward = func(x - h)
    return (fx_forward - fx_backward) / (2.0 * h)


def _run_newton_raphson(
    func: Callable[[float], float],
    x0: float,
    tol: float,
    max_iterations: int = 100,
) -> Tuple[List[NewtonRaphsonStep], float, float, int]:
    steps: List[NewtonRaphsonStep] = []
    x_n = x0

    for iteration in range(1, max_iterations + 1):
        fx = func(x_n)
        try:
            dfx = _numeric_derivative(func, x_n)
        except Exception as exc:
            raise ValueError(f"No fue posible evaluar la derivada en x = {x_n}: {exc}") from exc

        if not math.isfinite(dfx) or abs(dfx) < 1e-12:
            raise ValueError(f"La derivada es cero o no es finita en x = {x_n}.")

        x_next = x_n - fx / dfx
        if not math.isfinite(x_next):
            raise ValueError("La iteración generó un valor no finito. Ajusta el valor inicial.")

        error = abs(x_next - x_n)
        fx_next = func(x_next)
        steps.append(NewtonRaphsonStep(iteration, x_n, fx, dfx, x_next, error))

        if abs(fx_next) < tol or error < tol:
            return steps, x_next, fx_next, iteration

        x_n = x_next

    raise ValueError("El método excedió el máximo de iteraciones permitidas.")


class NewtonRootCard(bq.RootInputCard):
    def __init__(self, index: int):
        super().__init__(index)
        try:
            self.lbl_intervalo.hide()
            self.interval_widget.hide()
        except Exception:
            pass

        self.lbl_aprox.setText("Punto inicial x₀:")
        self.lbl_aprox.setToolTip("Valor desde el cual arrancará Newton-Raphson.")
        self.approx_edit.setPlaceholderText("Ejemplo: -1.25")

    def set_primary_mode(self, is_primary: bool) -> None:
        super().set_primary_mode(is_primary)
        for widget in (self.lbl_aprox, self.approx_edit):
            widget.setVisible(True)


class MetodoNewtonRaphsonWindow(bq.MetodoBiseccionWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Método de Newton-Raphson")
        try:
            self.btn_calcular.setText("Calcular Newton-Raphson")
        except Exception:
            pass
        self._update_static_labels()

    def _update_static_labels(self) -> None:
        replacements = {
            "Método de Bisección": "Método de Newton-Raphson",
            "MActodo de BisecciA3n": "Método de Newton-Raphson",
            (
                "Para la primera raíz ingresa f(x), el intervalo [a, b], la tolerancia y (opcional) un aproximado. "
                "Para las siguientes raíces solo ingresa el intervalo [a, b]."
            ): (
                "Para la primera raíz ingresa f(x), el punto inicial x₀ y la tolerancia. "
                "Las siguientes raíces solo requieren su propio x₀."
            ),
            (
                "Para la primera raA-z ingresa f(x), el intervalo [a, b], la tolerancia y (opcional) un aproximado. "
                "Para las siguientes raA-ces solo ingresa el intervalo [a, b]."
            ): (
                "Para la primera raíz ingresa f(x), el punto inicial x₀ y la tolerancia. "
                "Las siguientes raíces solo requieren su propio x₀."
            ),
            (
                "Puedes calcular hasta diez raíces reutilizando la misma f(x) y tolerancia de la primera. "
                "Cada intervalo validará que f(a) y f(b) tengan signos opuestos antes de iniciar."
            ): (
                "Puedes calcular hasta diez raíces reutilizando la misma f(x) y tolerancia. "
                "Si dejas x₀ vacío, la aplicación sugerirá candidatos detectando cambios de signo."
            ),
            (
                "Puedes calcular hasta diez raA-ces reutilizando la misma f(x) y tolerancia de la primera. "
                "Cada intervalo validarA� que f(a) y f(b) tengan signos opuestos antes de iniciar."
            ): (
                "Puedes calcular hasta diez raíces reutilizando la misma f(x) y tolerancia. "
                "Si dejas x₀ vacío, la aplicación sugerirá candidatos detectando cambios de signo."
            ),
        }
        for lbl in self.findChildren(QLabel):
            text = lbl.text() or ""
            if text in replacements:
                lbl.setText(replacements[text])
            elif "bisecci" in text.lower():
                lbl.setText("Método de Newton-Raphson")

    def _sync_root_cards(self):
        target = self.root_count.value()
        while len(self.root_cards) < target:
            card = NewtonRootCard(len(self.root_cards) + 1)
            self.root_cards.append(card)
            self.forms_layout.addWidget(card)
        while len(self.root_cards) > target:
            card = self.root_cards.pop()
            card.setParent(None)
        for idx, card in enumerate(self.root_cards, start=1):
            card.set_index(idx)
            card.set_primary_mode(idx == 1)
        for card in self.root_cards:
            for edit in (card.function_edit, card.approx_edit):
                try:
                    edit.textChanged.disconnect()
                except Exception:
                    pass
                try:
                    edit.textChanged.connect(self._update_plot_live)
                except Exception:
                    pass
        try:
            self._update_plot_live()
        except Exception:
            pass

    def _current_x_range(self):
        xs = []
        for card in self.root_cards:
            try:
                x0 = bq._parse_numeric(card.approx_edit.text().strip())
                xs.append(x0)
            except Exception:
                continue
        if xs:
            x_min, x_max = min(xs), max(xs)
            if x_min == x_max:
                pad = abs(x_min) * 0.5 if x_min != 0 else 5.0
                return x_min - pad, x_max + pad
            pad = (x_max - x_min) * 0.15
            return x_min - pad, x_max + pad
        return -10.0, 10.0

    def _update_plot_live(self):
        if not getattr(self, "_mpl_ready", False):
            return
        plt = self._mpl["plt"]
        ax = self._mpl["ax"]
        ax.clear()
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        ax.axhline(0.0, color="black", linewidth=0.9)
        x_min, x_max = self._current_x_range()
        try:
            import numpy as np
        except Exception:
            np = None
        num_points = 600
        if np is not None:
            xs = np.linspace(x_min, x_max, num_points)
        else:
            xs = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]

        plotted = False
        for idx, card in enumerate(self.root_cards, start=1):
            expr = (card.function_edit.text() or "").strip()
            if not expr:
                continue
            try:
                func = bq._compile_function(expr)
            except Exception:
                continue
            ys = []
            for x in xs:
                try:
                    y = func(float(x))
                except Exception:
                    y = float("nan")
                ys.append(y)
            ax.plot(xs, ys, label=f"f(x) #{idx}", linewidth=1.6, alpha=0.9)
            try:
                x0 = bq._parse_numeric(card.approx_edit.text().strip())
                ax.axvline(x0, color="#6E4B5E", linestyle=":", alpha=0.3)
            except Exception:
                pass
            plotted = True

        if plotted:
            ax.set_xlim(x_min, x_max)
            ax.legend()
            ax.set_title("Ajusta la función y los valores iniciales")
        else:
            ax.set_title("Escribe f(x) para previsualizar la curva")
        self._mpl["canvas"].draw_idle()

    def _draw_results_on_canvas(self, resultados):
        if not getattr(self, "_mpl_ready", False):
            return
        plt = self._mpl["plt"]
        ax = self._mpl["ax"]
        ax.clear()
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")
        ax.axhline(0.0, color="black", linewidth=0.9)

        ranges = []
        for (_idx, _expr, pasos, _raiz, _fc, _it, _ap) in resultados:
            xs = []
            for paso in pasos:
                xs.extend([paso.x, paso.x_next])
            if xs:
                ranges.append((min(xs), max(xs)))
        if ranges:
            x_min = min(r[0] for r in ranges)
            x_max = max(r[1] for r in ranges)
            span = x_max - x_min
            if span == 0:
                pad = abs(x_min) * 0.2 if x_min != 0 else 1.0
            else:
                pad = span * 0.12
            x_min -= pad
            x_max += pad
        else:
            x_min, x_max = self._current_x_range()

        try:
            import numpy as np
        except Exception:
            np = None
        num_points = 800
        if np is not None:
            xs = np.linspace(x_min, x_max, num_points)
        else:
            xs = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]

        colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", [])
        markers = ["o", "s", "^", "D", "v", "P", "X", "*", "+", "x"]

        for i, (idx, expr, pasos, raiz, _fc, _it, _ap) in enumerate(resultados):
            try:
                func = bq._compile_function(expr)
            except Exception:
                continue
            ys = []
            for x in xs:
                try:
                    y = func(float(x))
                except Exception:
                    y = float("nan")
                ys.append(y)
            color = colors[i % len(colors)] if colors else None
            ax.plot(xs, ys, label=f"f(x) #{idx}", color=color, linewidth=1.6, alpha=0.9)
            for paso in pasos:
                ax.scatter(paso.x, paso.fx, color=color, s=50, alpha=0.85)
            try:
                r_x = float(raiz)
                marker = markers[i % len(markers)]
                ax.plot(r_x, 0.0, marker=marker, color=color, markersize=10, label=f"Raíz {i+1}")
            except Exception:
                pass

        ax.set_xlim(x_min, x_max)
        ax.legend()
        ax.set_title("Resultados de Newton-Raphson")
        self._mpl["canvas"].draw_idle()

    def _create_table_widget(self, pasos: List[NewtonRaphsonStep]) -> QTableWidget:
        table = QTableWidget()
        headers = ["Iteración", "xₙ", "f(xₙ)", "f'(xₙ)", "xₙ₊₁", "Error |xₙ₊₁ - xₙ|"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(pasos))
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setObjectName("ResultsTable")
        table.setMinimumHeight(320)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        for row, paso in enumerate(pasos):
            values = [
                str(paso.iteration),
                bq._format_number(paso.x),
                bq._format_number(paso.fx),
                bq._format_number(paso.dfx),
                bq._format_number(paso.x_next),
                bq._format_number(paso.error),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        return table

    def _calcular(self):
        resultados: List[Tuple[int, str, List[NewtonRaphsonStep], float, float, int, None]] = []
        display_idx = 1
        skip_additional = False

        if not self.root_cards:
            QMessageBox.warning(self, "Aviso", "No hay formularios disponibles.")
            return

        first_card = self.root_cards[0]
        expr1, _a_txt, _b_txt, tol_txt, x0_txt = first_card.values()
        expr1 = (expr1 or "").strip()
        if not expr1:
            QMessageBox.warning(self, "Aviso", "Ingresa la función f(x) en la primera raíz.")
            return
        try:
            func = bq._compile_function(expr1)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"La función en la primera raíz no es válida: {exc}")
            return

        try:
            tol = bq._parse_numeric(tol_txt)
            if tol <= 0:
                raise ValueError("La tolerancia debe ser positiva.")
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Tolerancia inválida (primera raíz): {exc}")
            return

        guesses: List[float] = []
        if x0_txt:
            try:
                guesses.append(bq._parse_numeric(x0_txt))
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"Punto inicial inválido (primera raíz): {exc}")
                return
        else:
            dlg = bq.IntervalsDialog(self, func, start=-10.0, end=10.0, step=0.5)
            if dlg.exec() != QDialog.Accepted:
                return
            intervals = dlg.get_intervals()
            if not intervals:
                QMessageBox.warning(self, "Aviso", "No se detectaron intervalos con cambio de signo.")
                return
            guesses = [(a + b) / 2.0 for a, b in intervals]
            try:
                total = len(guesses)
                if total > 0 and self.root_count.value() < total:
                    self.root_count.setValue(total)
                for idx_i, guess in enumerate(guesses, start=1):
                    if idx_i - 1 < len(self.root_cards):
                        card_i = self.root_cards[idx_i - 1]
                        try:
                            card_i.approx_edit.setText(bq._format_number(guess))
                        except Exception:
                            pass
            except Exception:
                pass
            skip_additional = True

        any_success = False
        for guess in guesses:
            try:
                pasos, raiz, fc, iteraciones = _run_newton_raphson(func, guess, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                display_idx += 1
                any_success = True
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    f"No se logró converger desde x₀ = {bq._format_number(guess)}: {exc}",
                )
        if skip_additional and not any_success:
            QMessageBox.warning(self, "Aviso", "No se encontraron raíces con los valores sugeridos.")
            return

        if not skip_additional:
            for card_idx, card in enumerate(self.root_cards[1:], start=2):
                _expr, _a_txt, _b_txt, _tol_txt, x_txt = card.values()
                if not x_txt:
                    QMessageBox.warning(self, "Aviso", f"La raíz #{card_idx} no tiene punto inicial. Se omitirá.")
                    continue
                try:
                    x_guess = bq._parse_numeric(x_txt)
                except Exception as exc:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"Punto inicial inválido en la raíz #{card_idx}: {exc}",
                    )
                    continue
                try:
                    pasos, raiz, fc, iteraciones = _run_newton_raphson(func, x_guess, tol)
                    resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                    display_idx += 1
                except Exception as exc:
                    QMessageBox.warning(
                        self,
                        "Aviso",
                        f"No se pudo calcular la raíz #{card_idx} (x₀ = {x_guess}): {exc}",
                    )
                    continue

        unique_results = []
        seen = set()
        for item in resultados:
            try:
                key = round(float(item[3]), 10)
            except Exception:
                key = item[3]
            if key in seen:
                continue
            seen.add(key)
            unique_results.append(item)
        resultados = unique_results
        if not resultados:
            QMessageBox.information(self, "Resultados", "No se encontraron raíces.")
            return

        super()._render_resultados(resultados)
        self._adjust_result_cards(resultados, tol)
        try:
            self._draw_results_on_canvas(resultados)
        except Exception:
            pass

    def _adjust_result_cards(self, resultados, tol) -> None:
        cards = []
        for i in range(self.results_layout.count()):
            widget = self.results_layout.itemAt(i).widget()
            if widget is not None:
                cards.append(widget)
            if len(cards) >= len(resultados):
                break
        for card_widget, (_idx, _expr, pasos, raiz, fc, iteraciones, _ap) in zip(cards, resultados):
            labels = card_widget.findChildren(QLabel)
            summary_label = next((lbl for lbl in labels if "El método converge" in (lbl.text() or "")), None)
            if summary_label is not None:
                tol_txt = bq._format_number(tol)
                err = abs(fc)
                err_txt = bq._format_number(err)
                indicator = "✓ dentro del límite" if err <= tol else "✗ fuera del límite"
                summary_label.setText(
                    "\n".join(
                        [
                            f"El método converge con {iteraciones} iteraciones.",
                            f"La raíz es: {bq._format_number(raiz)}.",
                            f"Tolerancia: {tol_txt} — Error alcanzado: {err_txt} ({indicator})",
                        ]
                    )
                )
            start_label = next((lbl for lbl in labels if "Intervalo usado" in (lbl.text() or "")), None)
            if start_label is not None:
                if pasos:
                    x0 = pasos[0].x
                    start_label.setText(
                        f"Iteraciones generadas a partir de x₀ = {bq._format_number(x0)}."
                    )
                else:
                    start_label.setText("Iteraciones generadas desde tu punto inicial.")

