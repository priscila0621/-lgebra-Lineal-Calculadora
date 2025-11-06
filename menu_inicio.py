import os
import tkinter as tk
from tkinter import ttk


class MenuInicio:
    """
    Pantalla inicial (Tkinter) con dos opciones grandes:
    - Álgebra Lineal
    - Análisis Numérico

    Si existen imágenes en assets/selector/algebra.png y
    assets/selector/analisis.png se usan como ilustración.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora - Selección de módulo")
        # Ventana amplia para garantizar que el pie no se corte
        self.root.geometry("860x640")
        self.root.configure(bg="#fff7f9")

        # Estilos coherentes con el resto de la app
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Card.TFrame", background="#f7e7ea", relief="flat")
        style.configure("CardTitle.TLabel", font=("Segoe UI", 12, "bold"), background="#f7e7ea", foreground="#7a3d53")
        style.configure("Primary.TButton", font=("Segoe UI", 12, "bold"), padding=8, background="#fbb6ce", foreground="#fff")
        style.map("Primary.TButton",
                  background=[("!disabled", "#fbb6ce"), ("active", "#f472b6")],
                  foreground=[("!disabled", "white"), ("active", "white")])

        # Contenedor desplazable para garantizar visibilidad de créditos
        outer = tk.Frame(root, bg="#fff7f9")
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg="#fff7f9", highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg="#fff7f9")
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _sync_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            try:
                canvas.itemconfigure(content_id, width=canvas.winfo_width())
            except Exception:
                pass
        content.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", _sync_scrollregion)

        # Presentación: logo + nombre + descripción
        hero = ttk.Frame(content, style="Card.TFrame")
        hero.pack(padx=20, pady=(16, 6), fill="x")

        logo = tk.Canvas(hero, width=88, height=88, bg="#f7e7ea", highlightthickness=0)
        logo.pack(side="left", padx=12, pady=12)
        logo.create_oval(4, 4, 84, 84, fill="#B07A8C", outline="")
        logo.create_text(44, 44, text="NL", fill="white", font=("Segoe UI", 24, "bold"))

        head = ttk.Frame(hero, style="Card.TFrame")
        head.pack(side="left", padx=8, pady=10)
        ttk.Label(head, text="Nexus Linear — Calculadora Inteligente",
                  font=("Segoe UI", 18, "bold"), background="#f7e7ea", foreground="#7a3d53").pack(anchor="w")
        ttk.Label(head,
                  text=("Suite para álgebra lineal y análisis numérico. "
                        "Explora módulos especializados con resultados claros."),
                  font=("Segoe UI", 10), background="#f7e7ea", foreground="#6b4557",
                  wraplength=520).pack(anchor="w", pady=(4, 0))

        # Barra superior con engranaje de configuración
        topbar = ttk.Frame(content, style="Card.TFrame")
        topbar.pack(fill="x", padx=20, pady=(0, 0))
        gear_btn = tk.Button(topbar, text="⚙", bd=0, relief="flat", highlightthickness=0,
                             bg="#f7e7ea", activebackground="#f7e7ea", cursor="hand2",
                             command=self._open_config)
        gear_btn.pack(side="right", padx=(0, 4), pady=4)

        # Espaciadores superiores para centrar verticalmente las tarjetas
        spacer_top = ttk.Frame(content, style="Card.TFrame")
        spacer_top.pack(expand=True)

        # Contenedor de tarjetas
        cards = ttk.Frame(content, style="Card.TFrame")
        cards.configure(padding=18)
        cards.pack(padx=24, pady=12)

        inner = ttk.Frame(cards, style="Card.TFrame")
        inner.pack()

        # Carga opcional de imágenes
        self._img_algebra = self._load_image("assets/selector/algebra.png", size=(260, 260))
        self._img_analisis = self._load_image("assets/selector/analisis.png", size=(260, 260))

        # Tarjeta Álgebra
        frame_a = ttk.Frame(inner, style="Card.TFrame")
        frame_a.grid(row=0, column=0, padx=36, pady=16)
        panel_a = tk.Frame(frame_a, bg="#ffffff", highlightthickness=1, highlightbackground="#e2d5db")
        panel_a.pack(padx=8, pady=8)
        if self._img_algebra is not None:
            tk.Label(panel_a, image=self._img_algebra, bg="#ffffff").pack(padx=18, pady=18)
        else:
            ttk.Label(panel_a, text="Álgebra Lineal", style="CardTitle.TLabel").pack(padx=24, pady=32)
        ttk.Button(frame_a, text="Álgebra Lineal", style="Primary.TButton",
                   command=self._open_algebra, width=18).pack(pady=(6, 6))

        # Tarjeta Análisis Numérico
        frame_n = ttk.Frame(inner, style="Card.TFrame")
        frame_n.grid(row=0, column=1, padx=36, pady=16)
        panel_n = tk.Frame(frame_n, bg="#ffffff", highlightthickness=1, highlightbackground="#e2d5db")
        panel_n.pack(padx=8, pady=8)
        if self._img_analisis is not None:
            tk.Label(panel_n, image=self._img_analisis, bg="#ffffff").pack(padx=18, pady=18)
        else:
            ttk.Label(panel_n, text="Análisis Numérico", style="CardTitle.TLabel").pack(padx=24, pady=32)
        ttk.Button(frame_n, text="Análisis Numérico", style="Primary.TButton",
                   command=self._open_numerico, width=18).pack(pady=(6, 6))

        # Espaciador inferior para centrar el bloque de tarjetas
        spacer_bottom = ttk.Frame(content, style="Card.TFrame")
        spacer_bottom.pack(expand=True)

        # Acerca de (anclado abajo para que no se corte)
        about = ttk.Frame(content, style="Card.TFrame")
        about.pack(padx=24, pady=(8, 16), fill="x")
        ttk.Label(about, text="Acerca de", font=("Segoe UI", 12, "bold"),
                  background="#f7e7ea", foreground="#7a3d53").pack(anchor="w")
        self.lbl_copyright = ttk.Label(
            about,
            text=("© 2025 – Priscila Selva • Emma Serrano • Jeyni Orozco. "
                  "Todos los derechos reservados."),
            font=("Segoe UI", 9), background="#f7e7ea", foreground="#6b4557",
            wraplength=820, justify="left",
        )
        self.lbl_copyright.pack(anchor="w", pady=(4, 0))

        # Ajusta wraplength dinámicamente si cambia el tamaño de la ventana
        def _on_resize(event=None):
            try:
                w = max(300, canvas.winfo_width() - 60)
                self.lbl_copyright.configure(wraplength=w)
            except Exception:
                pass
        canvas.bind("<Configure>", _on_resize)

        # Desplazamiento con rueda del ratón (Windows)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _open_config(self):
        win = tk.Toplevel(self.root)
        win.title("Configuración")
        win.configure(bg="#fff7f9")
        win.geometry("420x260")
        ttk.Label(win, text="Opciones de configuración", font=("Segoe UI", 14, "bold"),
                  background="#fff7f9", foreground="#7a3d53").pack(pady=(16, 8))
        ttk.Label(
            win,
            text=("Aquí podrás ajustar preferencias de la aplicación.\n"
                  "Si te interesa, puedo añadir el tema claro/oscuro,\n"
                  "tamaños de fuente y más."),
            background="#fff7f9",
            foreground="#6b4557",
            justify="left",
        ).pack(padx=18, pady=(0, 16), anchor="w")
        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=(0, 12))

    def _load_image(self, relpath: str, size=(200, 200)):
        """Carga PNG/JPG si Pillow está disponible; si no, intenta con PhotoImage.
        Busca la ruta de forma robusta relativa al proyecto."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, relpath.replace("/", os.sep))
            if not os.path.exists(path):
                return None

            try:
                from PIL import Image, ImageTk  # type: ignore

                im = Image.open(path)
                im.thumbnail(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(im)
            except Exception:
                img = tk.PhotoImage(file=path)
                return img
        except Exception:
            return None

    def _open_algebra(self):
        from menu_algebra import MenuAlgebra
        # Mantener un solo root y usar Toplevel para conservar el icono en la barra de tareas
        try:
            self.root.withdraw()
            top = tk.Toplevel(self.root)

            def _on_close():
                try:
                    self.root.deiconify()
                finally:
                    top.destroy()

            top.protocol("WM_DELETE_WINDOW", _on_close)
            # MenuAlgebra no requiere callback; usa su propia navegación interna
            MenuAlgebra(top)
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass

    def _open_numerico(self):
        from menu_metodos_numericos import MenuMetodosNumericos
        try:
            self.root.withdraw()
            top = tk.Toplevel(self.root)

            def _on_close():
                try:
                    self.root.deiconify()
                finally:
                    top.destroy()

            top.protocol("WM_DELETE_WINDOW", _on_close)
            MenuMetodosNumericos(top, volver_callback=lambda: _on_close())
        except Exception:
            try:
                self.root.deiconify()
            except Exception:
                pass

    def _volver_selector(self, ventana_actual):
        # Mantener compatibilidad si se invoca este flujo
        try:
            ventana_actual.destroy()
        finally:
            try:
                self.root.deiconify()
            except Exception:
                pass
