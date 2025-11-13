import tkinter as tk
from tkinter import ttk, messagebox
from gauss_jordan_app import GaussJordanApp
from menu_matrices import MenuMatrices
from independencia_lineal import IndependenciaLinealApp
from transformaciones_lineales_app import TransformacionesLinealesApp
from menu_metodos_numericos import MenuMetodosNumericos

class MenuPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Álgebra Lineal")
        self.root.geometry("600x400")
        self.root.configure(bg="#ffe4e6")

        # ======================
        # Configuración de estilos (no se modificó nada más)
        # ======================
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Primary.TButton", font=("Segoe UI", 12, "bold"), padding=8,
                        background="#fbb6ce", foreground="#fff")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])

        style.configure("Back.TButton", font=("Segoe UI", 12, "bold"), padding=6,
                        background="#fecaca", foreground="#b91c1c")
        style.map("Back.TButton",
                  background=[("!disabled", "#fecaca"), ("active", "#fca5a5")],
                  foreground=[("!disabled", "#b91c1c"), ("active", "#7f1d1d")])

        # ======================
        # Interfaz principal
        # ======================
        ttk.Label(root, text="Calculadora Álgebra Lineal",
                  font=("Segoe UI", 20, "bold"), background="#ffe4e6",
                  foreground="#b91c1c").pack(pady=40)

        ttk.Button(root, text="Resolver sistema de ecuaciones lineales",
                   style="Primary.TButton", command=self.abrir_sistema).pack(pady=10)

        ttk.Button(root, text="Operaciones con matrices",
                   style="Primary.TButton", command=self.abrir_matrices).pack(pady=10)

        ttk.Button(root, text="Independencia lineal de vectores",
                   style="Primary.TButton", command=self.abrir_independencia_lineal).pack(pady=10)

        ttk.Button(root, text="Transformaciones lineales (T(x)=Ax)",
                   style="Primary.TButton", command=self.abrir_transformaciones).pack(pady=10)

        ttk.Button(root, text="Métodos Numéricos",
                   style="Primary.TButton", command=self.abrir_metodos_numericos).pack(pady=10)

    # ======================
    # Métodos
    # ======================
    def _abrir_toplevel(self, app_cls, descripcion: str):
        try:
            top = tk.Toplevel(self.root)

            def _on_close():
                try:
                    self.root.deiconify()
                finally:
                    top.destroy()

            top.protocol("WM_DELETE_WINDOW", _on_close)
            app_cls(top, volver_callback=lambda: (_on_close()))
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass

    def abrir_sistema(self):
        self._abrir_toplevel(GaussJordanApp, "Sistema de ecuaciones")

    def abrir_matrices(self):
        self._abrir_toplevel(MenuMatrices, "Operaciones con matrices")

    def abrir_independencia_lineal(self):
        self._abrir_toplevel(IndependenciaLinealApp, "Independencia lineal")

    def abrir_transformaciones(self):
        self._abrir_toplevel(TransformacionesLinealesApp, "Transformaciones lineales")

    def abrir_metodos_numericos(self):
        self._abrir_toplevel(MenuMetodosNumericos, "Métodos numéricos")

    def volver_inicio(self, ventana_actual):
        try:
            ventana_actual.destroy()
        finally:
            try:
                self.root.deiconify()
            except Exception:
                pass
