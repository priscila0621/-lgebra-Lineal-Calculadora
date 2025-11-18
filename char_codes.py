from pathlib import Path
path = Path(r"c:/Users/LPT-DELL/Documents/Calculadora/-Algebra-Lineal-Calculadora/qt_app/metodos/newton_raphson_qt.py")
text = path.read_text(encoding="utf-8")
target = "lneas"
match = "l" + text[text.index('l'):text.index('l')+6]
print([hex(ord(c)) for c in match])
