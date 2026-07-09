from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.models.field_box import FieldBox


class BoxEditor(ttk.LabelFrame):
    def __init__(self, master, on_change, on_delete, on_clear_mapping):
        super().__init__(master, text="Field Settings", style="Card.TLabelframe")
        self.on_change = on_change
        self.on_delete = on_delete
        self.on_clear_mapping = on_clear_mapping
        self.current_field: FieldBox | None = None
        self._updating = False

        self.column_var = tk.StringVar(value="Not assigned")
        self.font_size_var = tk.IntVar(value=36)
        self.align_var = tk.StringVar(value="left")
        self.rtl_var = tk.BooleanVar(value=False)

        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Selected column", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))
        ttk.Label(self, textvariable=self.column_var, style="Value.TLabel").grid(row=0, column=1, sticky="w", padx=10, pady=(10, 4))
        ttk.Label(self, text="Max font size", style="Muted.TLabel").grid(row=1, column=0, sticky="w", padx=10, pady=4)
        ttk.Spinbox(self, from_=6, to=72, textvariable=self.font_size_var, width=8).grid(row=1, column=1, sticky="w", padx=10, pady=4)
        ttk.Label(self, text="Alignment", style="Muted.TLabel").grid(row=2, column=0, sticky="w", padx=10, pady=4)
        ttk.Combobox(self, textvariable=self.align_var, values=["left", "center", "right"], state="readonly").grid(row=2, column=1, sticky="ew", padx=10, pady=4)
        ttk.Checkbutton(self, text="Enable RTL shaping", variable=self.rtl_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=4)
        ttk.Button(self, text="Apply Settings", style="Accent.TButton", command=self.apply_changes).grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 6))
        ttk.Button(self, text="Clear Mapping", command=self.clear_mapping).grid(row=5, column=0, sticky="ew", padx=(10, 5), pady=(0, 12))
        ttk.Button(self, text="Delete Box", command=self.delete_field).grid(row=5, column=1, sticky="ew", padx=(5, 10), pady=(0, 12))
        self.columnconfigure(1, weight=1)

    def set_field(self, field: FieldBox | None) -> None:
        self.current_field = field
        self._updating = True
        try:
            if field is None:
                self.column_var.set("Not assigned")
                self.font_size_var.set(36)
                self.align_var.set("left")
                self.rtl_var.set(False)
            else:
                self.column_var.set(field.excel_column or "Not assigned")
                self.font_size_var.set(field.font_size)
                self.align_var.set(field.align)
                self.rtl_var.set(field.rtl)
        finally:
            self._updating = False

    def update_column(self, column: str) -> None:
        self.column_var.set(column or "Not assigned")

    def apply_changes(self) -> None:
        if self.current_field is None or self._updating:
            return
        self.current_field.font_size = int(self.font_size_var.get())
        self.current_field.align = self.align_var.get()
        self.current_field.rtl = bool(self.rtl_var.get())
        self.on_change()

    def clear_mapping(self) -> None:
        if self.current_field is None:
            return
        self.on_clear_mapping()

    def delete_field(self) -> None:
        if self.current_field is None:
            return
        self.on_delete()
