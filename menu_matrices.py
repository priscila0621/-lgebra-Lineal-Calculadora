import tkinter as tk
from tkinter import ttk, messagebox
from suma_matrices_app import SumaMatricesApp
from resta_matrices_app import RestaMatricesApp
from multiplicacion_matrices_app import MultiplicacionMatricesApp
from transpuesta_matriz_app import TranspuestaMatrizApp
from inversa_matriz_app import InversaMatrizApp
from determinante_matriz_app import DeterminanteMatrizApp


class MenuMatrices:
    def __init__(self, root, volver_callback):
        self.root = root
        self.root.title("Operaciones con Matrices")
        self.root.geometry("620x460")
        self.root.configure(bg="#ffe4e6")
        self.volver_callback = volver_callback

        ttk.Label(
            root,
            text="Operaciones con Matrices",
            font=("Segoe UI", 18, "bold"),
            background="#ffe4e6",
            foreground="#b91c1c",
        ).pack(pady=24)

        botones = (
            ("Suma de matrices", self.suma_matrices),
            ("Resta de matrices", self.resta_matrices),
            ("Multiplicación de matrices", self.multiplicacion_matrices),
            ("Determinantes", self.determinante_matriz),
            ("Inversa de matriz", self.inversa_matriz),
            ("Transpuesta de matriz", self.transpuesta_matriz),
        )

        for texto, comando in botones:
            ttk.Button(self.root, text=texto, style="Primary.TButton", command=comando).pack(pady=8)

        self.frame_volver_fijo = ttk.Frame(root)
        self.frame_volver_fijo.pack(side="bottom", fill="x", pady=(12, 0))
        self.boton_volver = ttk.Button(
            self.frame_volver_fijo,
            text="Volver al inicio",
            style="Back.TButton",
            command=self.volver_callback,
        )
        self.boton_volver.pack(pady=10)

    def _abrir_operacion(self, app_cls, descripcion):
        try:
            self.root.withdraw()
            top = tk.Toplevel(self.root)
            # Si el usuario cierra la ventana con la X, restaurar esta ventana
            def _on_close():
                try:
                    self.root.deiconify()
                finally:
                    top.destroy()
            top.protocol("WM_DELETE_WINDOW", _on_close)
            app_cls(top, volver_callback=self.volver_callback)
        except Exception as exc:
            try:
                self.root.deiconify()
            except Exception:
                pass
            messagebox.showerror("Error", f"Ocurrió un error al abrir {descripcion}: {exc}")
        finally:
            try:
                self.boton_volver.lift()
            except Exception:
                pass

    def suma_matrices(self):
        self._abrir_operacion(SumaMatricesApp, "Suma de matrices")

    def resta_matrices(self):
        self._abrir_operacion(RestaMatricesApp, "Resta de matrices")

    def multiplicacion_matrices(self):
        self._abrir_operacion(MultiplicacionMatricesApp, "Multiplicación de matrices")

    def determinante_matriz(self):
        self._abrir_operacion(DeterminanteMatrizApp, "Determinantes")

    def inversa_matriz(self):
        self._abrir_operacion(InversaMatrizApp, "Inversa de matriz")

    def transpuesta_matriz(self):
        self._abrir_operacion(TranspuestaMatrizApp, "Transpuesta de matriz")

