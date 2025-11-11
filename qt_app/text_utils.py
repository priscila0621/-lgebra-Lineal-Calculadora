import re


_SUP_MAP = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "j": "ʲ", "t": "ᵗ", "T": "ᵀ",
    # Common capitals occasionally used as superscripts in math contexts
    "N": "ᴺ", "I": "ᴵ",
}


def _to_sup(text: str) -> str:
    return "".join(_SUP_MAP.get(ch, ch) for ch in (text or ""))


def superscriptify(expr: str) -> str:
    """
    Convert caret-based exponent notations in a plain string into Unicode
    superscripts for nicer display in Qt labels or table cells.

    Supported forms:
    - x^(2) -> x²
    - x^(-3) -> x⁻³
    - A^{-1} -> A⁻¹
    - R^n -> Rⁿ
    - ^T / ^t -> ᵀ / ᵗ
    """
    if not expr:
        return expr

    s = str(expr)

    # ^{...}
    s = re.sub(r"\^\{([^}]*)\}", lambda m: _to_sup(m.group(1)), s)

    # ^(...)
    s = re.sub(r"\^\(([^)]*)\)", lambda m: _to_sup(m.group(1)), s)

    # ^-?\d+
    s = re.sub(r"\^([+-]?\d+)", lambda m: _to_sup(m.group(1)), s)

    # ^ followed by a single common letter
    s = re.sub(r"\^([nNijItT])", lambda m: _to_sup(m.group(1)), s)

    return s

