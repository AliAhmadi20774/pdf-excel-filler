from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from PIL import ImageTk

from app.core.pdf_renderer import PdfRenderer
from app.core.pdf_renderer import RenderedPage
from app.models.field_box import FieldBox


class PdfViewer(ttk.Frame):
    def __init__(self, master, on_select: Callable[[str | None], None]):
        super().__init__(master)
        self.on_select = on_select
        self.renderer: PdfRenderer | None = None
        self.zoom = 1.25
        self.page_index = 0
        self.current_page_size: tuple[float, float] = (1.0, 1.0)
        self.current_image_size: tuple[int, int] = (1, 1)
        self.image_origin: tuple[float, float] = (24.0, 24.0)
        self.fields: list[FieldBox] = []
        self.selected_field_id: str | None = None
        self.tk_image = None
        self._preloaded_page: RenderedPage | None = None
        self._drag_start: tuple[int, int] | None = None
        self._active_rect: int | None = None

        controls = ttk.Frame(self, style="Toolbar.TFrame")
        controls.pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Zoom -", command=self.zoom_out).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Zoom +", command=self.zoom_in).pack(side="left")
        ttk.Button(controls, text="Previous", command=lambda: self.change_page(-1)).pack(side="left", padx=(12, 4))
        ttk.Button(controls, text="Next", command=lambda: self.change_page(1)).pack(side="left")
        self.page_label = ttk.Label(controls, text="Page -/-", style="Value.TLabel")
        self.page_label.pack(side="left", padx=12)

        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(canvas_frame, background="#dbe4f0", highlightthickness=0, bd=0)
        self.h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)

    def load_pdf(self, pdf_path: str) -> None:
        if self.renderer is not None:
            self.renderer.close()
        self.renderer = PdfRenderer(pdf_path)
        self.page_index = 0
        self.render()

    def set_renderer(self, renderer: PdfRenderer, preloaded_page: RenderedPage | None = None) -> None:
        if self.renderer is not None:
            self.renderer.close()
        self.renderer = renderer
        self.page_index = 0
        self._preloaded_page = preloaded_page
        self.render()

    def set_fields(self, fields: list[FieldBox]) -> None:
        self.fields = fields
        self.render()

    def render(self) -> None:
        self.canvas.delete("all")
        if self.renderer is None:
            return
        if self._preloaded_page is not None and self._preloaded_page.page_index == self.page_index:
            page = self._preloaded_page
            self._preloaded_page = None
        else:
            page = self.renderer.render_page(self.page_index, zoom=self.zoom)
        self.current_page_size = (page.width, page.height)
        self.current_image_size = page.image.size
        self.tk_image = ImageTk.PhotoImage(page.image)

        shadow_left = self.image_origin[0] - 10
        shadow_top = self.image_origin[1] - 10
        shadow_right = self.image_origin[0] + self.current_image_size[0] + 10
        shadow_bottom = self.image_origin[1] + self.current_image_size[1] + 10
        self.canvas.create_rectangle(
            shadow_left,
            shadow_top,
            shadow_right,
            shadow_bottom,
            fill="#f8fbff",
            outline="#b8c6d9",
            width=1,
        )
        self.canvas.create_image(self.image_origin[0], self.image_origin[1], anchor="nw", image=self.tk_image)
        self.page_label.configure(text=f"Page {self.page_index + 1}/{self.renderer.page_count}")
        self._draw_fields()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _draw_fields(self) -> None:
        scale_x = self.current_image_size[0] / self.current_page_size[0]
        scale_y = self.current_image_size[1] / self.current_page_size[1]
        for field in self.fields:
            if field.page_index != self.page_index:
                continue
            x1 = self.image_origin[0] + (field.x * scale_x)
            y1 = self.image_origin[1] + (field.y * scale_y)
            x2 = self.image_origin[0] + ((field.x + field.width) * scale_x)
            y2 = self.image_origin[1] + ((field.y + field.height) * scale_y)
            color = "#c62828" if field.id == self.selected_field_id else "#1565c0"
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2, tags=("field", field.id))
            self.canvas.create_text(
                x1 + 6,
                y1 + 6,
                anchor="nw",
                text=field.excel_column or field.id,
                fill=color,
                tags=("field", field.id),
                font=("Segoe UI", 9, "bold"),
            )

    def _to_canvas_point(self, event) -> tuple[int, int]:
        return int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))

    def _hit_test(self, x: int, y: int) -> str | None:
        hits = self.canvas.find_overlapping(x, y, x, y)
        for item in hits:
            tags = self.canvas.gettags(item)
            if len(tags) >= 2 and tags[0] == "field":
                return tags[1]
        return None

    def _on_press(self, event) -> None:
        canvas_x, canvas_y = self._to_canvas_point(event)
        hit = self._hit_test(canvas_x, canvas_y)
        if hit:
            self.selected_field_id = hit
            self.on_select(hit)
            self.render()
            return
        self.selected_field_id = None
        self.on_select(None)
        self.render()
        self._drag_start = (canvas_x, canvas_y)
        self._active_rect = self.canvas.create_rectangle(
            canvas_x,
            canvas_y,
            canvas_x,
            canvas_y,
            outline="#2e7d32",
            width=2,
            dash=(4, 2),
        )

    def _on_drag(self, event) -> None:
        if self._drag_start and self._active_rect:
            canvas_x, canvas_y = self._to_canvas_point(event)
            self.canvas.coords(self._active_rect, self._drag_start[0], self._drag_start[1], canvas_x, canvas_y)

    def _on_release(self, event) -> None:
        if not self._drag_start or not self._active_rect:
            return
        x1, y1 = self._drag_start
        x2, y2 = self._to_canvas_point(event)
        self.canvas.delete(self._active_rect)
        self._active_rect = None
        self._drag_start = None
        if abs(x2 - x1) < 8 or abs(y2 - y1) < 8:
            return
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        field = self._create_field_from_canvas(left, top, right, bottom)
        self.fields.append(field)
        self.selected_field_id = field.id
        self.on_select(field.id)
        self.render()

    def _create_field_from_canvas(self, left: int, top: int, right: int, bottom: int) -> FieldBox:
        scale_x = self.current_page_size[0] / self.current_image_size[0]
        scale_y = self.current_page_size[1] / self.current_image_size[1]
        image_left = self.image_origin[0]
        image_top = self.image_origin[1]
        image_right = image_left + self.current_image_size[0]
        image_bottom = image_top + self.current_image_size[1]

        bounded_left = min(max(left, image_left), image_right)
        bounded_right = min(max(right, image_left), image_right)
        bounded_top = min(max(top, image_top), image_bottom)
        bounded_bottom = min(max(bottom, image_top), image_bottom)

        index = len(self.fields) + 1
        return FieldBox(
            id=f"field_{index:03d}",
            page_index=self.page_index,
            x=(bounded_left - image_left) * scale_x,
            y=(bounded_top - image_top) * scale_y,
            width=max((bounded_right - bounded_left) * scale_x, 1.0),
            height=max((bounded_bottom - bounded_top) * scale_y, 1.0),
            font_size=36,
            rtl=False,
        )

    def _on_right_click(self, event) -> None:
        canvas_x, canvas_y = self._to_canvas_point(event)
        hit = self._hit_test(canvas_x, canvas_y)
        if not hit:
            return
        self.fields[:] = [field for field in self.fields if field.id != hit]
        if self.selected_field_id == hit:
            self.selected_field_id = None
            self.on_select(None)
        self.render()

    def change_page(self, delta: int) -> None:
        if self.renderer is None:
            return
        next_page = self.page_index + delta
        if 0 <= next_page < self.renderer.page_count:
            self.page_index = next_page
            self.render()

    def zoom_in(self) -> None:
        self.zoom = min(self.zoom + 0.25, 4.0)
        self.render()

    def zoom_out(self) -> None:
        self.zoom = max(self.zoom - 0.25, 0.5)
        self.render()
