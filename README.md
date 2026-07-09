# PDF Excel Filler

Desktop application for filling a fixed PDF template with row-based Excel data.

## What It Does

The app lets a user:

1. Open a PDF template.
2. Draw boxes on top of the PDF pages.
3. Open an Excel file with column headers.
4. Map each drawn box to an Excel column.
5. Generate one output PDF per Excel row.

The original PDF is never modified directly. The app creates text overlays and merges them into copies of the source PDF.

## Current Features

- Open a PDF and render pages inside a Tkinter desktop UI
- Draw rectangular boxes directly on the PDF preview
- Store box coordinates in real PDF units
- Map boxes to Excel columns from a sidebar list
- Save and load template JSON files
- Generate one output PDF for each Excel row
- Optional RTL text shaping for Persian or Arabic content
- Dynamic font sizing so text stays inside the box

## Project Structure

```text
pdf-excel-filler/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── core/
│   ├── models/
│   └── ui/
├── assets/
│   └── fonts/
├── output/
├── samples/
├── templates/
└── tests/
```

## Installation

The project is intended to use the local virtual environment in `.venv`.

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe main.py
```

## Build Windows EXE

```powershell
.\.venv\Scripts\pyinstaller.exe --onefile --windowed --add-data "assets;assets" main.py
```

The generated executable is placed in `dist/main.exe`.

## Notes About Persian Text

- The UI is in English.
- PDF content can still be Persian.
- For correct Persian rendering, place a suitable Persian font such as `Vazirmatn-Regular.ttf` in `assets/fonts/`.
- If the selected field needs RTL shaping, enable `Enable RTL shaping` in the field settings panel.

## Sample Files

Test assets are available in `samples/`:

- `samples/test_template.pdf`
- `samples/test_data.xlsx`

## Testing

Run tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
