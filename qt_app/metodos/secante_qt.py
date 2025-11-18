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
class SecantStep:
    iteration: int
    x_prev: float
    x_curr: float
    fx_prev: float
    fx_curr: float
    x_next: float
    error: float

    # Propiedades compatibles con las vistas heredadas
    @property
    def a(self) -> float:
        return self.x_prev

    @property
    def b(self) -> float:
        return self.x_curr

    @property
    def c(self) -> float:
        return self.x_next

    @property
    def fa(self) -> float:
        return self.fx_prev

    @property
    def fb(self) -> float:
        return self.fx_curr

    @property
    def fc(self) -> float:
        return self.fx_curr


def _run_secante(
    func: Callable[[float], float],
    x0: float,
    x1: float,
    tol: float,
    max_iterations: int = 100,
) -> Tuple[List[SecantStep], float, float, int]:
    steps: List[SecantStep] = []
    x_prev, x_curr = x0, x1

    for iteration in range(1, max_iterations + 1):
        fx_prev = func(x_prev)
        fx_curr = func(x_curr)

        denom = fx_prev - fx_curr
        if not math.isfinite(denom) or abs(denom) < 1e-12:
            raise ValueError("El denominador f(x_n-1) - f(x_n) es cero o no es finito.")

        x_next = x_curr - fx_curr * (x_prev - x_curr) / denom
        if not math.isfinite(x_next):
            raise ValueError("La iteracion genero un valor no finito. Ajusta los valores iniciales.")

        error = abs(x_next - x_curr)
        fx_next = func(x_next)
        steps.append(SecantStep(iteration, x_prev, x_curr, fx_prev, fx_curr, x_next, error))

        if abs(fx_next) < tol or error < tol:
            return steps, x_next, fx_next, iteration

        x_prev, x_curr = x_curr, x_next

    raise ValueError("El metodo excedio el maximo de iteraciones permitidas.")


def _suggest_pairs_without_sign_change(
    func: Callable[[float], float],
    start: float,
    end: float,
    step: float,
    limit: int = 6,
) -> List[Tuple[float, float]]:
    """Genera pares (x0, x1) sin exigir cambio de signo, priorizando |f(x)| pequeños pero evitando tomar la raíz exacta."""
    if step <= 0:
        raise ValueError("El paso debe ser positivo.")
    if start > end:
        start, end = end, start
    samples = []
    x = start
    # Evitar bucles infinitos por errores de precisión
    max_iter = 10000
    count = 0
    while x <= end + 1e-12 and count < max_iter:
        try:
            fx = func(x)
            if math.isfinite(fx):
                samples.append((x, fx))
        except Exception:
            pass
        x += step
        count += 1
    # Evitar usar puntos donde f(x) ≈ 0 para no arrancar en la raíz exacta (sin iteraciones).
    eps = 1e-8
    filtered = [(x, fx) for x, fx in samples if abs(fx) >= eps]
    if len(filtered) < 2:
        return []
    pairs = []
    for i in range(len(filtered) - 1):
        x0, f0 = filtered[i]
        x1, f1 = filtered[i + 1]
        score = abs(f0) + abs(f1)
        pairs.append((score, (x0, x1)))
    pairs.sort(key=lambda t: t[0])
    unique = []
    seen = set()
    for _, pair in pairs:
        key = (round(pair[0], 6), round(pair[1], 6))
        if key in seen:
            continue
        seen.add(key)
        unique.append(pair)
        if len(unique) >= limit:
            break
    return unique


def _dedup_pairs_by_mid(intervals: List[Tuple[float, float]], ndigits: int = 6) -> List[Tuple[float, float]]:
    """Elimina pares que apunten al mismo punto medio (para no repetir la misma raíz)."""
    seen = set()
    unique = []
    for a, b in intervals:
        mid = round((a + b) / 2.0, ndigits)
        if mid in seen:
            continue
        seen.add(mid)
        unique.append((a, b))
    return unique


class SecantRootCard(bq.RootInputCard):
    def __init__(self, index: int):
        super().__init__(index)
        # Reutilizamos el intervalo como par de puntos iniciales x0, x1.
        try:
            self.lbl_intervalo.setText("Valores iniciales x0 y x1:")
            self.lbl_intervalo.setToolTip("No es necesario que f(x) cambie de signo entre ellos.")
            labels = self.interval_widget.findChildren(QLabel)
            if len(labels) >= 2:
                labels[0].setText("x0 =")
                labels[1].setText("x1 =")
            self.a_edit.setPlaceholderText("Ejemplo: -1.2")
            self.a_edit.setToolTip("Primera aproximacion (x0).")
            self.b_edit.setPlaceholderText("Ejemplo: 0.8")
            self.b_edit.setToolTip("Segunda aproximacion (x1).")
        except Exception:
            pass

        self.lbl_aprox.hide()
        self.approx_edit.hide()

    def set_primary_mode(self, is_primary: bool) -> None:
        # Mantener f(x) y tolerancia solo en la primera tarjeta.
        super().set_primary_mode(is_primary)
        self.lbl_aprox.hide()
        self.approx_edit.hide()


class MetodoSecanteWindow(bq.MetodoBiseccionWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Metodo de la secante")
        try:
            self.btn_calcular.setText("Calcular secante")
        except Exception:
            pass
        self._update_static_labels()

    def _update_static_labels(self) -> None:
        replacements = {
            "Metodo de Biseccion": "Metodo de la secante",
            "M\u00c9todo de Bisecci\u00d3n": "Metodo de la secante",
            (
                "Para la primera raiz ingresa f(x), el intervalo [a, b], la tolerancia y (opcional) un aproximado. "
                "Para las siguientes raices solo ingresa el intervalo [a, b]."
            ): (
                "Para la primera raiz ingresa f(x), los valores x0 y x1 y la tolerancia. "
                "Las siguientes raices solo requieren sus propios x0 y x1."
            ),
        }
        for lbl in self.findChildren(QLabel):
            text = lbl.text() or ""
            if text in replacements:
                lbl.setText(replacements[text])
            elif "bisecci" in text.lower():
                lbl.setText("Metodo de la secante")

    def _sync_root_cards(self):
        target = self.root_count.value()
        while len(self.root_cards) < target:
            card = SecantRootCard(len(self.root_cards) + 1)
            self.root_cards.append(card)
            self.forms_layout.addWidget(card)
        while len(self.root_cards) > target:
            card = self.root_cards.pop()
            card.setParent(None)
        for idx, card in enumerate(self.root_cards, start=1):
            card.set_index(idx)
            card.set_primary_mode(idx == 1)
        for card in self.root_cards:
            for edit in (card.function_edit, card.a_edit, card.b_edit):
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
            for edit in (card.a_edit, card.b_edit):
                try:
                    value = bq._parse_numeric(edit.text().strip())
                    xs.append(value)
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
        if not getattr(self, "_mpl_ready", False) or not self.root_cards:
            return

        expr = (self.root_cards[0].function_edit.text() or "").strip()
        if not expr:
            return
        try:
            func = bq._compile_function(expr)
        except Exception:
            return

        plt = self._mpl["plt"]
        ax = self._mpl["ax"]
        ax.clear()
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.axhline(0.0, color="black", linewidth=0.9)
        ax.set_xlabel("Eje X")
        ax.set_ylabel("Eje Y")

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

        ys = []
        for x in xs:
            try:
                y = func(float(x))
            except Exception:
                y = float("nan")
            ys.append(y)
        ax.plot(xs, ys, label="f(x)", color="#b91c1c", linewidth=1.6, alpha=0.9)

        # Marcar puntos iniciales del primer formulario
        first = self.root_cards[0]
        try:
            x0 = bq._parse_numeric(first.a_edit.text().strip())
            x1 = bq._parse_numeric(first.b_edit.text().strip())
            ax.scatter([x0, x1], [func(x0), func(x1)], color="#374151", s=60, zorder=5, label="Puntos iniciales")
        except Exception:
            pass

        ax.legend()
        ax.set_title("Vista previa metodo de la secante")
        self._mpl["canvas"].draw_idle()

    def _create_table_widget(self, pasos: List[SecantStep]) -> QTableWidget:
        table = QTableWidget()
        headers = [
            "Iteracion",
            "x(n-1)",
            "x(n)",
            "f(x(n-1))",
            "f(x(n))",
            "x(n+1)",
            "Error |x(n+1)-x(n)|",
        ]
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
                bq._format_number(paso.x_prev),
                bq._format_number(paso.x_curr),
                bq._format_number(paso.fx_prev),
                bq._format_number(paso.fx_curr),
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
        resultados: List[Tuple[int, str, List[SecantStep], float, float, int, None]] = []
        display_idx = 1

        if not self.root_cards:
            QMessageBox.warning(self, "Aviso", "No hay formularios disponibles.")
            return

        first_card = self.root_cards[0]
        expr1, a_txt, b_txt, tol_txt, _ = first_card.values()
        expr1 = (expr1 or "").strip()
        if not expr1:
            QMessageBox.warning(self, "Aviso", "Ingresa la funcion f(x) en la primera raiz.")
            return
        try:
            func = bq._compile_function(expr1)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"La funcion en la primera raiz no es valida: {exc}")
            return

        try:
            tol = bq._parse_numeric(tol_txt)
            if tol <= 0:
                raise ValueError("La tolerancia debe ser positiva.")
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Tolerancia invalida (primera raiz): {exc}")
            return

        # 1) Construir lista de pares candidatos si no se ingresan manualmente.
        candidate_pairs: List[Tuple[float, float]] = []
        try:
            candidate_pairs = bq._detect_sign_change_intervals(func, -10.0, 10.0, 0.5)
        except Exception:
            candidate_pairs = []
        if not candidate_pairs:
            try:
                candidate_pairs = _suggest_pairs_without_sign_change(func, -10.0, 10.0, 0.5)
            except Exception:
                candidate_pairs = []
        candidate_pairs = _dedup_pairs_by_mid(candidate_pairs)

        # 2) Armamos la lista final de semillas por tarjeta.
        seeds: List[Tuple[float, float]] = []
        card_count = self.root_count.value()
        for idx, card in enumerate(self.root_cards):
            _expr, xa_txt, xb_txt, _tol_txt, _ = card.values()
            if xa_txt and xb_txt:
                try:
                    x0 = bq._parse_numeric(xa_txt)
                    x1 = bq._parse_numeric(xb_txt)
                    seeds.append((x0, x1))
                    continue
                except Exception as exc:
                    QMessageBox.warning(self, "Aviso", f"Puntos iniciales invalidos en la raiz #{idx+1}: {exc}")
                    continue
            # Tomar candidatos auto si están disponibles
            if idx < len(candidate_pairs):
                x0, x1 = candidate_pairs[idx]
                seeds.append((x0, x1))
                try:
                    card.a_edit.setText(bq._format_number(x0))
                    card.b_edit.setText(bq._format_number(x1))
                except Exception:
                    pass
            else:
                QMessageBox.information(
                    self,
                    "Aviso",
                    f"No hay pares automáticos suficientes para la raiz #{idx+1}. Ajusta el rango o ingresa x0 y x1.",
                )

        # Si tenemos menos seeds que tarjetas, ajustar el contador para no mostrar tarjetas vacías.
        if seeds and card_count < len(seeds):
            try:
                self.root_count.setValue(len(seeds))
            except Exception:
                pass

        for x0_i, x1_i in seeds:
            try:
                pasos, raiz, fc, iteraciones = _run_secante(func, x0_i, x1_i, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                display_idx += 1
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    f"No se pudo converger desde x0={bq._format_number(x0_i)}, x1={bq._format_number(x1_i)}: {exc}",
                )

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
            QMessageBox.information(self, "Resultados", "No se encontraron raices.")
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
            summary_label = next(
                (
                    lbl
                    for lbl in labels
                    if any(keyword in (lbl.text() or "").lower() for keyword in ("converge", "intervalo"))
                ),
                None,
            )
            if summary_label is not None:
                tol_txt = bq._format_number(tol)
                err = abs(fc)
                err_txt = bq._format_number(err)
                indicator = "dentro del limite" if err <= tol else "fuera del limite"
                summary_lines = [
                    f"El metodo converge con {iteraciones} iteraciones.",
                    f"La raiz es: {bq._format_number(raiz)}.",
                    f"Tolerancia: {tol_txt} — Error alcanzado: {err_txt} ({indicator})",
                ]
                try:
                    if pasos:
                        x0 = pasos[0].x_prev
                        x1 = pasos[0].x_curr
                        summary_lines.insert(1, f"Puntos iniciales: x0 = {bq._format_number(x0)}, x1 = {bq._format_number(x1)}.")
                except Exception:
                    pass
                summary_label.setText("\n".join(summary_lines))

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
                xs.extend([paso.x_prev, paso.x_curr, paso.x_next])
            if xs:
                ranges.append((min(xs), max(xs)))
        if ranges:
            x_min = min(r[0] for r in ranges)
            x_max = max(r[1] for r in ranges)
            span = x_max - x_min
            pad = (span * 0.12) if span != 0 else (abs(x_min) * 0.2 if x_min != 0 else 1.0)
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
            xs_plot = np.linspace(x_min, x_max, num_points)
        else:
            xs_plot = [x_min + (x_max - x_min) * i / (num_points - 1) for i in range(num_points)]

        colors = plt.rcParams.get("axes.prop_cycle").by_key().get("color", [])
        markers = ["o", "s", "^", "D", "v", "P", "X", "*", "+", "x"]

        for i, (idx, expr, pasos, raiz, _fc, _it, _ap) in enumerate(resultados):
            try:
                func = bq._compile_function(expr)
            except Exception:
                continue
            ys = []
            for x in xs_plot:
                try:
                    y = func(float(x))
                except Exception:
                    y = float("nan")
                ys.append(y)
            color = colors[i % len(colors)] if colors else None
            ax.plot(xs_plot, ys, label=f"f(x) #{idx}", color=color, linewidth=1.6, alpha=0.9)

            iter_color = "#555555"
            for paso in pasos:
                ax.scatter([paso.x_prev, paso.x_curr], [paso.fx_prev, paso.fx_curr], color=iter_color, s=50, alpha=0.9, zorder=5)
                try:
                    ax.plot(
                        [paso.x_prev, paso.x_curr],
                        [paso.fx_prev, paso.fx_curr],
                        color=iter_color,
                        linestyle=(0, (3, 3)),
                        linewidth=1.0,
                        alpha=0.7,
                        zorder=3,
                    )
                except Exception:
                    pass
                try:
                    ax.plot(
                        [paso.x_curr, paso.x_next],
                        [paso.fx_curr, 0.0],
                        color=iter_color,
                        linestyle="--",
                        alpha=0.8,
                        linewidth=1.0,
                        zorder=4,
                    )
                    ax.scatter(paso.x_next, 0.0, color=iter_color, s=36, alpha=0.9, zorder=5)
                except Exception:
                    pass

            try:
                r_x = float(raiz)
                marker = markers[i % len(markers)]
                ax.scatter([r_x], [0.0], marker=marker, color=color, s=120, label=f"Raiz {i+1}", zorder=6)
            except Exception:
                pass

        ax.set_xlim(x_min, x_max)
        ax.legend()
        ax.set_title("Resultados - Metodo de la secante")
        self._mpl["canvas"].draw_idle()
