from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Callable

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.core.text_utils import prepare_text
from app.models.field_box import FieldBox
from app.models.template_config import TemplateConfig


class PdfGenerator:
    def __init__(self, font_dir: str | Path | None = None):
        self.font_dir = Path(font_dir) if font_dir else None
        self._registered_fonts: set[str] = set()

    def generate(
        self,
        config: TemplateConfig,
        rows: list[dict],
        output_dir: str | Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        created_files: list[Path] = []
        total = len(rows)
        for index, row in enumerate(rows, start=1):
            target = output_path / f"output_{index:03d}.pdf"
            self._generate_single(config, row, target)
            created_files.append(target)
            if progress_callback is not None:
                progress_callback(index, total)
        return created_files

    def _generate_single(self, config: TemplateConfig, row: dict, target: Path) -> None:
        reader = PdfReader(config.pdf_file)
        writer = PdfWriter(clone_from=config.pdf_file)
        for page_index, page in enumerate(reader.pages):
            page_fields = [field for field in config.fields if field.page_index == page_index]
            overlay = self._build_overlay(page, page_fields, row)
            if overlay is not None:
                writer.pages[page_index].merge_page(overlay)
        with target.open("wb") as file_handle:
            writer.write(file_handle)

    def _build_overlay(self, page, fields: list[FieldBox], row: dict):
        if not fields:
            return None
        packet = io.BytesIO()
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        overlay_canvas = canvas.Canvas(packet, pagesize=(page_width, page_height))
        overlay_canvas.setFillColor(Color(0, 0, 0, 1))
        for field in fields:
            value = row.get(field.excel_column, "")
            text = prepare_text(value, rtl=field.rtl)
            font_name = self._resolve_font(field.font_name)
            font_size = self._fit_font_size(text, font_name, field)
            overlay_canvas.setFont(font_name, font_size)
            self._draw_text(overlay_canvas, text, field, page_height, font_name, font_size)
        overlay_canvas.save()
        packet.seek(0)
        return PdfReader(packet).pages[0]

    def _draw_text(
        self,
        overlay_canvas: canvas.Canvas,
        text: str,
        field: FieldBox,
        page_height: float,
        font_name: str,
        font_size: int,
    ) -> None:
        inner_padding_x = min(4.0, max(field.width * 0.08, 2.0))
        inner_padding_y = min(3.0, max(field.height * 0.08, 1.0))
        inner_width = max(field.width - (inner_padding_x * 2), 1.0)
        inner_height = max(field.height - (inner_padding_y * 2), 1.0)
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)

        top_left_y = field.y
        bottom_left_y = page_height - (top_left_y + field.height)
        baseline_y = bottom_left_y + inner_padding_y + max((inner_height - font_size) / 2, 0) + (font_size * 0.18)

        if field.align == "center":
            draw_x = field.x + inner_padding_x + max((inner_width - text_width) / 2, 0)
        elif field.align == "left":
            draw_x = field.x + inner_padding_x
        else:
            draw_x = field.x + field.width - inner_padding_x - text_width

        min_x = field.x + inner_padding_x
        max_x = max(min_x, field.x + field.width - inner_padding_x - text_width)
        draw_x = min(max(draw_x, min_x), max_x)
        overlay_canvas.drawString(draw_x, baseline_y, text)

    def _fit_font_size(self, text: str, font_name: str, field: FieldBox) -> int:
        width_limit = max(field.width - 8, 1)
        height_limit = max(field.height - 4, 6)
        max_size = max(6, int(field.font_size))
        if not text:
            return min(max_size, int(height_limit))
        for size in range(max_size, 5, -1):
            text_width = pdfmetrics.stringWidth(text, font_name, size)
            if text_width <= width_limit and size <= height_limit:
                return size
        return 6

    def _resolve_font(self, preferred_name: str) -> str:
        if preferred_name in pdfmetrics.getRegisteredFontNames():
            return preferred_name
        if self.font_dir:
            candidate = self.font_dir / f"{preferred_name}-Regular.ttf"
            if not candidate.exists():
                candidate = self.font_dir / f"{preferred_name}.ttf"
            if candidate.exists() and preferred_name not in self._registered_fonts:
                pdfmetrics.registerFont(TTFont(preferred_name, str(candidate)))
                self._registered_fonts.add(preferred_name)
                return preferred_name
        return "Helvetica"

    @staticmethod
    def safe_filename(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "output"
