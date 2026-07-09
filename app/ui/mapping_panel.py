from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class MappingPanel(ttk.LabelFrame):
    def __init__(self, master, on_select):
        super().__init__(master, text="Excel Columns", style="Card.TLabelframe")
        self.on_select = on_select
        self.list_var = tk.StringVar(value=[])
        self.listbox = tk.Listbox(
            self,
            listvariable=self.list_var,
            height=14,
            activestyle="none",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            selectbackground="#2a6df4",
            selectforeground="#ffffff",
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=8)
        self.listbox.bind("<<ListboxSelect>>", self._handle_select)

    def set_columns(self, columns: list[str]) -> None:
        self.list_var.set(columns)

    def _handle_select(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.on_select(self.listbox.get(selection[0]))
