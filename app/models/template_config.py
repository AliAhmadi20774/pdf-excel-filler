from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.models.field_box import FieldBox


@dataclass
class TemplateConfig:
    template_name: str
    pdf_file: str
    page_count: int
    fields: list[FieldBox] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "template_name": self.template_name,
            "pdf_file": self.pdf_file,
            "page_count": self.page_count,
            "fields": [field_box.to_dict() for field_box in self.fields],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateConfig":
        return cls(
            template_name=data["template_name"],
            pdf_file=data["pdf_file"],
            page_count=data["page_count"],
            fields=[FieldBox.from_dict(item) for item in data.get("fields", [])],
        )

    @property
    def pdf_path(self) -> Path:
        return Path(self.pdf_file)
