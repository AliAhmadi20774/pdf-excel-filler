from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class FieldBox:
    id: str
    page_index: int
    label: str = ""
    excel_column: str = ""
    x: float = 0.0
    y: float = 0.0
    width: float = 120.0
    height: float = 24.0
    font_name: str = "Vazirmatn"
    font_size: int = 36
    align: str = "left"
    rtl: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FieldBox":
        return cls(**data)
