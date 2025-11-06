import tkinter as tk
from tkinter import ttk
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

    def abrir_sistema(self):
        self.root.destroy()
        root2 = tk.Tk()
        GaussJordanApp(root2, lambda: self.volver_inicio(root2))
        root2.mainloop()

    def abrir_matrices(self):
        self.root.destroy()
        root2 = tk.Tk()
        MenuMatrices(root2, lambda: self.volver_inicio(root2))
        root2.mainloop()

    def abrir_independencia_lineal(self):
        self.root.destroy()
        root2 = tk.Tk()
        IndependenciaLinealApp(root2, lambda: self.volver_inicio(root2))
        root2.mainloop()

    def abrir_transformaciones(self):
        self.root.destroy()
        root2 = tk.Tk()
        TransformacionesLinealesApp(root2, lambda: self.volver_inicio(root2))
        root2.mainloop()

    def volver_inicio(self, ventana_actual):
        ventana_actual.destroy()
        root = tk.Tk()
        MenuAlgebra(root)
        root.mainloop()

