from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.core.excel_reader import ExcelReader
from app.core.pdf_generator import PdfGenerator
from app.core.template_manager import TemplateManager
from app.models.field_box import FieldBox
from app.models.template_config import TemplateConfig
from app.ui.box_editor import BoxEditor
from app.ui.mapping_panel import MappingPanel
from app.ui.pdf_viewer import PdfViewer


BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
FONT_DIR = BASE_DIR / "assets" / "fonts"


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PDF Excel Filler")
        self.root.geometry("1480x920")

        self.template_manager = TemplateManager()
        self.generator = PdfGenerator(font_dir=FONT_DIR)

        self.pdf_path: Path | None = None
        self.excel_path: Path | None = None
        self.excel_columns: list[str] = []
        self.excel_rows: list[dict] = []
        self.fields: list[FieldBox] = []
        self.output_base_dir: Path = OUTPUT_DIR

        self._build()

    def _build(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=16)
        shell.pack(fill="both", expand=True)

        header = ttk.Frame(shell, style="Hero.TFrame", padding=(18, 16))
        header.pack(fill="x", pady=(0, 14))
        ttk.Label(header, text="PDF Excel Filler", style="HeroTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Draw boxes over a PDF, map them to Excel columns, and generate one filled PDF per row.",
            style="HeroText.TLabel",
            wraplength=920,
        ).pack(anchor="w", pady=(6, 0))

        toolbar = ttk.Frame(shell, style="Toolbar.TFrame", padding=12)
        toolbar.pack(fill="x", pady=(0, 12))
        ttk.Button(toolbar, text="Open PDF", style="Accent.TButton", command=self.choose_pdf).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Open Excel", command=self.choose_excel).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Generate Output", style="Accent.TButton", command=self.generate_output).pack(side="left", padx=4)

        content = ttk.Panedwindow(shell, orient="horizontal")
        content.pack(fill="both", expand=True)

        self.viewer = PdfViewer(content, on_select=self.handle_field_select)
        content.add(self.viewer, weight=5)

        sidebar = ttk.Frame(content, style="Sidebar.TFrame", padding=12)
        content.add(sidebar, weight=2)

        status_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        status_card.pack(fill="x", pady=(0, 10))
        ttk.Label(status_card, text="Status", style="SectionTitle.TLabel").pack(anchor="w")
        self.status_var = tk.StringVar(value="Open a PDF and an Excel file to begin.")
        ttk.Label(status_card, textvariable=self.status_var, style="Status.TLabel", wraplength=320, justify="left").pack(fill="x", pady=(6, 0))

        output_card = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        output_card.pack(fill="x", pady=(0, 10))
        ttk.Label(output_card, text="Output", style="SectionTitle.TLabel").pack(anchor="w")
        self.output_dir_var = tk.StringVar(value=str(self.output_base_dir))
        ttk.Label(output_card, text="Base folder", style="Muted.TLabel").pack(anchor="w", pady=(6, 2))
        ttk.Label(output_card, textvariable=self.output_dir_var, style="Path.TLabel", wraplength=320, justify="left").pack(fill="x")
        output_actions = ttk.Frame(output_card, style="Card.TFrame")
        output_actions.pack(fill="x", pady=(10, 0))
        ttk.Button(output_actions, text="Change Folder", command=self.choose_output_directory).pack(side="left")
        ttk.Button(output_actions, text="Open Folder", command=self.open_output_directory).pack(side="left", padx=(8, 0))

        self.box_editor = BoxEditor(
            sidebar,
            on_change=self.refresh_view,
            on_delete=self.delete_selected_field,
            on_clear_mapping=self.clear_selected_mapping,
        )
        self.box_editor.pack(fill="x", pady=(0, 8))

        self.mapping_panel = MappingPanel(sidebar, on_select=self.assign_selected_column)
        self.mapping_panel.pack(fill="both", expand=True)
        self.root.bind("<Delete>", self._handle_delete_key)

    def choose_pdf(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self.pdf_path = Path(path)
        self.fields = []
        self.viewer.load_pdf(str(self.pdf_path))
        self.viewer.set_fields(self.fields)
        self.status_var.set(f"Loaded PDF: {self.pdf_path.name}")

    def choose_excel(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xlsm")])
        if not path:
            return
        self.excel_path = Path(path)
        reader = ExcelReader(self.excel_path)
        self.excel_columns = reader.read_columns()
        self.excel_rows = reader.read_rows()
        self.mapping_panel.set_columns(self.excel_columns)
        self.status_var.set(f"Loaded Excel: {self.excel_path.name} | {len(self.excel_rows)} rows")

    def choose_output_directory(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self.output_base_dir))
        if not selected:
            return
        self.output_base_dir = Path(selected)
        self.output_dir_var.set(str(self.output_base_dir))
        self.status_var.set(f"Output base folder changed to: {self.output_base_dir}")

    def open_output_directory(self) -> None:
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(self.output_base_dir)  # type: ignore[attr-defined]
        except OSError:
            messagebox.showinfo("Output Folder", str(self.output_base_dir))

    def open_generated_directory(self, target_dir: Path) -> None:
        try:
            os.startfile(target_dir)  # type: ignore[attr-defined]
        except OSError:
            messagebox.showinfo("Generated Folder", str(target_dir))

    def handle_field_select(self, field_id: str | None) -> None:
        field = next((item for item in self.fields if item.id == field_id), None)
        self.box_editor.set_field(field)
        if field is not None:
            self.status_var.set(f"Selected box: {field.excel_column or field.id}")
        else:
            self.status_var.set("No box selected.")

    def refresh_view(self) -> None:
        self.viewer.set_fields(self.fields)

    def assign_selected_column(self, column: str) -> None:
        field_id = self.viewer.selected_field_id
        if field_id is None:
            self.status_var.set("Select a box on the PDF first, then click a column on the right.")
            return
        field = next((item for item in self.fields if item.id == field_id), None)
        if field is None:
            return
        field.excel_column = column
        field.label = column
        self.box_editor.update_column(column)
        self.viewer.selected_field_id = None
        self.box_editor.set_field(None)
        self.refresh_view()
        self.status_var.set(f"Mapped selected box to column: {column}")

    def delete_selected_field(self) -> None:
        field_id = self.viewer.selected_field_id
        if field_id is None:
            self.status_var.set("Select a box first if you want to delete it.")
            return
        self.fields = [field for field in self.fields if field.id != field_id]
        self.viewer.selected_field_id = None
        self.box_editor.set_field(None)
        self.refresh_view()
        self.status_var.set("Selected box deleted.")

    def _handle_delete_key(self, _event=None) -> None:
        self.delete_selected_field()

    def clear_selected_mapping(self) -> None:
        field_id = self.viewer.selected_field_id
        if field_id is None:
            self.status_var.set("Select a box first if you want to clear its mapping.")
            return
        field = next((item for item in self.fields if item.id == field_id), None)
        if field is None:
            return
        field.excel_column = ""
        field.label = ""
        self.box_editor.update_column("")
        self.refresh_view()
        self.status_var.set(f"Mapping cleared for {field_id}.")

    def build_template(self) -> TemplateConfig:
        if self.pdf_path is None or self.viewer.renderer is None:
            raise ValueError("No PDF selected.")
        return TemplateConfig(
            template_name=self.pdf_path.stem,
            pdf_file=str(self.pdf_path),
            page_count=self.viewer.renderer.page_count,
            fields=self.fields,
        )

    def save_template(self) -> None:
        try:
            config = self.build_template()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=TEMPLATES_DIR,
            filetypes=[("JSON files", "*.json")],
        )
        if not path:
            return
        self.template_manager.save(config, path)
        self.status_var.set(f"Template saved: {Path(path).name}")

    def load_template(self) -> None:
        path = filedialog.askopenfilename(initialdir=TEMPLATES_DIR, filetypes=[("JSON files", "*.json")])
        if not path:
            return
        config = self.template_manager.load(path)
        self.pdf_path = Path(config.pdf_file)
        self.fields = config.fields
        self.viewer.load_pdf(str(self.pdf_path))
        self.viewer.set_fields(self.fields)
        self.status_var.set(f"Template loaded: {Path(path).name}")

    def generate_output(self) -> None:
        if self.pdf_path is None:
            messagebox.showerror("Error", "Open a PDF first.")
            return
        if self.excel_path is None:
            messagebox.showerror("Error", "Open an Excel file first.")
            return
        if not self.fields:
            messagebox.showerror("Error", "Draw at least one box on the PDF.")
            return
        missing = [field.id for field in self.fields if not field.excel_column]
        if missing:
            messagebox.showerror("Error", f"These boxes are still not mapped to an Excel column: {', '.join(missing)}")
            return
        config = self.build_template()
        target_dir = self._build_run_output_dir()
        created = self.generator.generate(config, self.excel_rows, target_dir)
        self.status_var.set(f"Generated {len(created)} PDF files in: {target_dir}")
        self.open_generated_directory(target_dir)
        messagebox.showinfo("Done", f"Generated {len(created)} PDF files.\n\nSaved in:\n{target_dir}")

    def _build_run_output_dir(self) -> Path:
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        stem = self.pdf_path.stem if self.pdf_path else "export"
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target_dir = self.output_base_dir / f"{stem}_{timestamp}"
        target_dir.mkdir(parents=True, exist_ok=False)
        return target_dir


def configure_styles(root: tk.Tk) -> None:
    root.configure(bg="#eef3f8")
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    style.configure("App.TFrame", background="#eef3f8")
    style.configure("Hero.TFrame", background="#16324f")
    style.configure("Toolbar.TFrame", background="#eef3f8")
    style.configure("Sidebar.TFrame", background="#eef3f8")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("Card.TLabelframe", background="#ffffff", borderwidth=0)
    style.configure("Card.TLabelframe.Label", background="#ffffff", foreground="#18324a", font=("Segoe UI", 11, "bold"))
    style.configure("TLabel", background="#eef3f8", foreground="#18324a", font=("Segoe UI", 10))
    style.configure("HeroTitle.TLabel", background="#16324f", foreground="#ffffff", font=("Segoe UI Semibold", 20))
    style.configure("HeroText.TLabel", background="#16324f", foreground="#c7d6e6", font=("Segoe UI", 10))
    style.configure("SectionTitle.TLabel", background="#ffffff", foreground="#18324a", font=("Segoe UI Semibold", 11))
    style.configure("Status.TLabel", background="#ffffff", foreground="#425466", font=("Segoe UI", 10))
    style.configure("Path.TLabel", background="#ffffff", foreground="#24415f", font=("Consolas", 9))
    style.configure("Muted.TLabel", background="#ffffff", foreground="#5c7188", font=("Segoe UI", 9))
    style.configure("Value.TLabel", background="#ffffff", foreground="#18324a", font=("Segoe UI Semibold", 10))
    style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
    style.configure("Accent.TButton", background="#2a6df4", foreground="#ffffff")
    style.map(
        "Accent.TButton",
        background=[("active", "#1f5dd0"), ("pressed", "#184aa6")],
        foreground=[("disabled", "#dce7ff"), ("!disabled", "#ffffff")],
    )


def main() -> None:
    root = tk.Tk()
    configure_styles(root)
    MainWindow(root)
    root.mainloop()
