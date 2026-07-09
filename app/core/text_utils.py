from __future__ import annotations

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:  # pragma: no cover
    arabic_reshaper = None
    get_display = None


def prepare_text(value: object, rtl: bool = False) -> str:
    text = "" if value is None else str(value)
    if not rtl:
        return text
    if arabic_reshaper is None or get_display is None:
        return text
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
