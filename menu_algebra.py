import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from gauss_jordan_app import GaussJordanApp
from menu_matrices import MenuMatrices
from independencia_lineal import IndependenciaLinealApp
from transformaciones_lineales_app import TransformacionesLinealesApp


class MenuAlgebra:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Álgebra Lineal")
        self.root.geometry("600x400")
        self.root.configure(bg="#ffe4e6")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=8,
            background="#fbb6ce",
            foreground="#fff",
        )
        style.map(
            "Primary.TButton",
            background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
            foreground=[("!disabled", "white"), ("active", "white")],
        )

        ttk.Label(
            root,
            text="Calculadora Álgebra Lineal",
            font=("Segoe UI", 20, "bold"),
            background="#ffe4e6",
            foreground="#b91c1c",
        ).pack(pady=40)

        ttk.Button(
            root,
            text="Resolver sistema de ecuaciones lineales",
            style="Primary.TButton",
            command=self.abrir_sistema,
        ).pack(pady=10)

        ttk.Button(
            root,
            text="Operaciones con matrices",
            style="Primary.TButton",
            command=self.abrir_matrices,
        ).pack(pady=10)

        ttk.Button(
            root,
            text="Independencia lineal de vectores",
            style="Primary.TButton",
            command=self.abrir_independencia_lineal,
        ).pack(pady=10)

        ttk.Button(
            root,
            text="Transformaciones lineales (T(x)=Ax)",
            style="Primary.TButton",
            command=self.abrir_transformaciones,
        ).pack(pady=10)

    def _abrir_toplevel(self, app_cls, descripcion: str):
        try:
            # Ocultar la ventana padre para asegurar que la nueva ventana quede visible
            try:
                self.root.withdraw()
            except Exception:
                pass

            top = tk.Toplevel(self.root)

            # Al cerrar la ventana hija con la X, restaurar el root
            def _on_close():
                try:
                    self.root.deiconify()
                finally:
                    top.destroy()

            top.protocol("WM_DELETE_WINDOW", _on_close)

            # Pasar callback de volver
            app_cls(top, volver_callback=lambda: (_on_close()))
        except Exception as exc:
            # Mostrar el error al usuario para facilitar depuración
            try:
                self.root.deiconify()
            except Exception:
                pass
            tb = traceback.format_exc()
            messagebox.showerror("Error", f"Error al abrir {descripcion}: {exc}\n\n{tb}")

    def abrir_sistema(self):
        self._abrir_toplevel(GaussJordanApp, "Sistema de ecuaciones")

    def abrir_matrices(self):
        self._abrir_toplevel(MenuMatrices, "Operaciones con matrices")

    def abrir_independencia_lineal(self):
        self._abrir_toplevel(IndependenciaLinealApp, "Independencia lineal")

    def abrir_transformaciones(self):
        self._abrir_toplevel(TransformacionesLinealesApp, "Transformaciones lineales")

    # Compatibilidad hacia atrás si alguna parte del código aún llama a esto
    def volver_inicio(self, ventana_actual):
        try:
            ventana_actual.destroy()
        finally:
            try:
                self.root.deiconify()
            except Exception:
                pass

