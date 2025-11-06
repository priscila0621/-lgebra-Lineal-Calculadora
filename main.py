"""
Punto de entrada de la app.
Si PySide6 está disponible, se usa la interfaz Qt (más moderna).
Si no, se usa la interfaz Tk existente como respaldo.
"""


def _run_qt():
    from qt_app.main_qt import run
    run()


def _run_tk():
    import tkinter as tk
    # Cargamos un selector inicial para elegir
    # entre Álgebra Lineal y Análisis Numérico
    from menu_inicio import MenuInicio
    root = tk.Tk()
    MenuInicio(root)
    root.mainloop()


if __name__ == "__main__":
    # Solo hacemos fallback a Tk cuando PySide6 no está disponible.
    # Si PySide6 está instalado pero hay un error en la ruta Qt,
    # dejamos que la excepción se muestre en consola para poder depurar.
    try:
        import PySide6  # noqa: F401
    except Exception:
        print("[INFO] PySide6 no encontrado; iniciando interfaz Tk.")
        _run_tk()
    else:
        _run_qt()

