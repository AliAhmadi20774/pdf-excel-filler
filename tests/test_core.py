from __future__ import annotations

from pathlib import Path

import fitz
from openpyxl import Workbook
from reportlab.pdfgen import canvas

from app.core.excel_reader import ExcelReader
from app.core.pdf_generator import PdfGenerator
from app.core.template_manager import TemplateManager
from app.models.field_box import FieldBox
from app.models.template_config import TemplateConfig


def create_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(595, 842))
    pdf.drawString(50, 800, "Template")
    pdf.save()


def create_excel(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["name", "national_id"])
    sheet.append(["Ali Rezaei", "0012345678"])
    sheet.append(["Maryam Ahmadi", "0098765432"])
    workbook.save(path)


def test_excel_reader(tmp_path: Path) -> None:
    excel_path = tmp_path / "data.xlsx"
    create_excel(excel_path)
    reader = ExcelReader(excel_path)
    assert reader.read_columns() == ["name", "national_id"]
    rows = reader.read_rows()
    assert len(rows) == 2
    assert rows[0]["name"] == "Ali Rezaei"


def test_template_manager_roundtrip(tmp_path: Path) -> None:
    config = TemplateConfig(
        template_name="demo",
        pdf_file="demo.pdf",
        page_count=1,
        fields=[FieldBox(id="field_001", page_index=0, label="name", excel_column="name")],
    )
    path = tmp_path / "template.json"
    manager = TemplateManager()
    manager.save(config, path)
    loaded = manager.load(path)
    assert loaded.template_name == "demo"
    assert loaded.fields[0].excel_column == "name"
    assert loaded.fields[0].rtl is False


def test_pdf_generator_creates_files(tmp_path: Path) -> None:
    pdf_path = tmp_path / "template.pdf"
    excel_path = tmp_path / "data.xlsx"
    output_dir = tmp_path / "output"
    create_pdf(pdf_path)
    create_excel(excel_path)
    rows = ExcelReader(excel_path).read_rows()
    config = TemplateConfig(
        template_name="demo",
        pdf_file=str(pdf_path),
        page_count=1,
        fields=[
            FieldBox(
                id="field_001",
                page_index=0,
                label="name",
                excel_column="name",
                x=100,
                y=100,
                width=180,
                height=24,
            )
        ],
    )
    generator = PdfGenerator()
    files = generator.generate(config, rows, output_dir)
    assert len(files) == 2
    assert files[0].exists()


def test_pdf_generator_shrinks_font_to_fit() -> None:
    generator = PdfGenerator()
    field = FieldBox(id="field_001", page_index=0, width=60, height=12, font_size=36)
    size = generator._fit_font_size("A very long value", "Helvetica", field)
    assert 6 <= size <= 12


def test_pdf_generator_places_text_inside_expected_box(tmp_path: Path) -> None:
    pdf_path = tmp_path / "template.pdf"
    output_dir = tmp_path / "output"
    create_pdf(pdf_path)
    config = TemplateConfig(
        template_name="demo",
        pdf_file=str(pdf_path),
        page_count=1,
        fields=[
            FieldBox(
                id="field_001",
                page_index=0,
                excel_column="name",
                x=100,
                y=100,
                width=180,
                height=24,
                font_size=24,
                align="left",
            )
        ],
    )
    generator = PdfGenerator()
    [created] = generator.generate(config, [{"name": "Aligned Text"}], output_dir)

    document = fitz.open(created)
    try:
        words = document[0].get_text("words")
    finally:
        document.close()

    aligned_word = next(word for word in words if "Aligned" in word[4])
    x0, y0, x1, y1 = aligned_word[:4]
    assert 100 <= x0 <= 110
    assert 95 <= y0 <= 120
    assert x1 <= 280
    assert y1 <= 126
