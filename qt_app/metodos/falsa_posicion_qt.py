from dataclasses import dataclass
from typing import Callable, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMessageBox, QMainWindow, QDialog

from . import biseccion_qt as bq


@dataclass
class FalsePositionStep:
    iteration: int
    a: float
    b: float
    c: float
    fa: float
    fb: float
    fc: float


def _run_false_position(
    func: Callable[[float], float],
    a: float,
    b: float,
    tol: float,
    max_iterations: int = 1000,
) -> Tuple[List[FalsePositionStep], float, float, int]:
    fa = func(a)
    fb = func(b)
    if not (fa * fb < 0):
        raise ValueError("El intervalo inicial debe contener la raíz (f(a) * f(b) < 0).")

    steps: List[FalsePositionStep] = []
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        # c = b - f(b) * (b - a) / (f(b) - f(a))
        c = b - fb * (b - a) / (fb - fa)
        fc = func(c)
        steps.append(FalsePositionStep(iteration, a, b, c, fa, fb, fc))

        if abs(fc) < tol:
            return steps, c, fc, iteration

        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc

    raise ValueError("El método excedió el máximo de iteraciones permitidas.")


class MetodoFalsaPosicionWindow(bq.MetodoBiseccionWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ajustar títulos y textos al método
        self.setWindowTitle("Método de Falsa Posición")
        try:
            # Cambiar el título visible dentro de la tarjeta principal
            for lbl in self.findChildren(QLabel):
                txt = (lbl.text() or "").strip().lower()
                if "bisecci" in txt:
                    lbl.setText("Método de Falsa Posición")
        except Exception:
            pass
        try:
            self.btn_calcular.setText("Calcular falsa posición")
        except Exception:
            pass

    def _calcular(self):
        resultados = []
        display_idx = 1

        if not self.root_cards:
            QMessageBox.warning(self, "Aviso", "No hay formularios disponibles.")
            return

        first_card = self.root_cards[0]
        expr1, a1_txt, b1_txt, tol1_txt, approx1_txt = first_card.values()
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
            tol = bq._parse_numeric(tol1_txt)
            if tol <= 0:
                raise ValueError("La tolerancia debe ser positiva.")
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Tolerancia inválida (primera raíz): {exc}")
            return

        approx1_value = None
        if approx1_txt:
            try:
                approx1_value = bq._parse_numeric(approx1_txt)
            except Exception:
                approx1_value = None

        # Primera raíz: permite detección automática si no hay [a,b]
        if a1_txt and b1_txt:
            try:
                a1 = bq._parse_numeric(a1_txt)
                b1 = bq._parse_numeric(b1_txt)
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"Intervalo inválido (primera raíz): {exc}")
                return
            try:
                pasos, raiz, fc, iteraciones = _run_false_position(func, a1, b1, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, approx1_value))
                display_idx += 1
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"No se pudo calcular la raíz (intervalo [{a1}, {b1}]): {exc}")
        else:
            dlg = bq.IntervalsDialog(self, func, start=-10.0, end=10.0, step=0.5)
            if dlg.exec() != QDialog.Accepted:
                return
            intervals = dlg.get_intervals()
            if not intervals:
                QMessageBox.warning(self, "Aviso", "No se detectaron intervalos donde la función cambie de signo.")
                return
            # Rellenar los text boxes de los intervalos detectados en las tarjetas
            try:
                total = len(intervals)
                if total > 0:
                    if self.root_count.value() < total:
                        self.root_count.setValue(total)
                    for idx_i, (a_det, b_det) in enumerate(intervals, start=1):
                        if idx_i - 1 < len(self.root_cards):
                            card_i = self.root_cards[idx_i - 1]
                            try:
                                card_i.a_edit.setText(bq._format_number(a_det))
                                card_i.b_edit.setText(bq._format_number(b_det))
                            except Exception:
                                pass
            except Exception:
                pass
            any_success = False
            for a, b in intervals:
                try:
                    pasos, raiz, fc, iteraciones = _run_false_position(func, a, b, tol)
                    resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, approx1_value))
                    display_idx += 1
                    any_success = True
                except Exception as exc:
                    QMessageBox.warning(self, "Aviso", f"Falsa posición en [{a}, {b}] falló: {exc}")
                    continue
            if not any_success:
                QMessageBox.warning(self, "Aviso", "No se encontraron raíces en los intervalos detectados.")
                return

        # Raíces adicionales: reutilizan expr1 y tol
        for card_idx, card in enumerate(self.root_cards[1:], start=2):
            _expr, a_txt, b_txt, _tol_txt, _approx_txt = card.values()
            if not (a_txt and b_txt):
                QMessageBox.warning(self, "Aviso", f"La raíz #{card_idx} no tiene intervalo. Se omitirá.")
                continue
            try:
                a = bq._parse_numeric(a_txt)
                b = bq._parse_numeric(b_txt)
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"Intervalo inválido en la raíz #{card_idx}: {exc}")
                continue
            try:
                pasos, raiz, fc, iteraciones = _run_false_position(func, a, b, tol)
                resultados.append((display_idx, expr1, pasos, raiz, fc, iteraciones, None))
                display_idx += 1
            except Exception as exc:
                QMessageBox.warning(self, "Aviso", f"No se pudo calcular la raíz #{card_idx} (intervalo [{a}, {b}]): {exc}")
                continue

        # Quitar duplicados por valor de ra�z
        _unique_res = []
        _seen_keys = set()
        for _it in resultados:
            try:
                _key = round(float(_it[3]), 10)
            except Exception:
                _key = _it[3]
            if _key in _seen_keys:
                continue
            _seen_keys.add(_key)
            _unique_res.append(_it)
        resultados = _unique_res
        if not resultados:
            QMessageBox.information(self, "Resultados", "No se encontraron raíces para los intervalos ingresados.")
            return

        self._render_resultados(resultados)
        try:
            self._draw_results_on_canvas(resultados)
        except Exception:
            pass
