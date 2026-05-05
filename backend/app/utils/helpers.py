def normalize_symbol(symbol: str) -> str:
    return (symbol or "").strip().upper()


def round_money(value: float, places: int = 2) -> float:
    return round(float(value), places)
