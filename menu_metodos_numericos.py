import tkinter as tk
from tkinter import ttk, messagebox


class MenuMetodosNumericos:
    def __init__(self, root, volver_callback):
        self.root = root
        self.root.title("Métodos Numéricos")
        self.root.geometry("620x320")
        self.root.configure(bg="#ffe4e6")
        self.volver_callback = volver_callback

        ttk.Label(
            root,
            text="Métodos Numéricos",
            font=("Segoe UI", 18, "bold"),
            background="#ffe4e6",
            foreground="#b91c1c",
        ).pack(pady=24)

        botones = (
            ("Método de Bisección", self.metodo_biseccion),
        )

        for texto, comando in botones:
            ttk.Button(self.root, text=texto, style="Primary.TButton", command=comando).pack(pady=8)

        self.frame_volver_fijo = ttk.Frame(root)
        self.frame_volver_fijo.pack(side="bottom", fill="x", pady=(12, 0))
        ttk.Button(
            self.frame_volver_fijo,
            text="Volver al inicio",
            style="Back.TButton",
            command=self.volver_callback,
        ).pack(pady=10)

    def metodo_biseccion(self):
        messagebox.showinfo(
            "Método de Bisección",
            "Esta funcionalidad estará disponible pronto.",
        )
