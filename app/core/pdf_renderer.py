from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image


@dataclass
class RenderedPage:
    page_index: int
    width: float
    height: float
    image: Image.Image


class PdfRenderer:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.document = fitz.open(self.pdf_path)

    @property
    def page_count(self) -> int:
        return self.document.page_count

    def get_page_size(self, page_index: int) -> tuple[float, float]:
        page = self.document[page_index]
        rect = page.rect
        return rect.width, rect.height

    def render_page(self, page_index: int, zoom: float = 1.25) -> RenderedPage:
        page = self.document[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        rect = page.rect
        return RenderedPage(page_index=page_index, width=rect.width, height=rect.height, image=image)

    def close(self) -> None:
        self.document.close()
