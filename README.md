# PDF Excel Filler

`PDF Excel Filler` is a desktop tool for filling a fixed PDF template with row-based data from an Excel file.

The application is designed for cases where:

- the PDF layout is already finalized
- the user wants to place text visually by drawing boxes on the PDF
- each Excel row should produce a separate output PDF

The source PDF is never edited in place. The app generates text overlays and merges them into copied output files.

## Current Capabilities

- Open and preview multi-page PDF files inside a Tkinter desktop UI
- Draw text boxes directly on top of the PDF preview
- Store box positions in real PDF coordinates
- Select an Excel column from the right-side column list for each box
- Edit a box after drawing it
- Delete a wrong box and redraw it
- Remove or change a column mapping later
- Generate one output PDF per Excel row
- Auto-fit font size so text stays inside the target box
- Optional RTL shaping for Persian and Arabic text
- Keep the UI in English while still allowing Persian text in generated PDFs
- Show loading/progress dialogs for heavy PDFs and large Excel files
- Open the generated output folder automatically after generation

## How It Works

1. Open a PDF template.
2. Open an Excel file.
3. Draw one or more boxes on the PDF preview.
4. Select each box and assign it to an Excel column.
5. Adjust font size, alignment, and RTL behavior if needed.
6. Click `Generate Output`.
7. The app creates one PDF per Excel row.

## Output Behavior

- In development mode, output is stored under `output/`
- In the packaged `.exe`, output is stored next to the executable by default
- Each generation run creates a timestamped folder, so previous files are not overwritten

Example output folder name:

```text
test_template_20260709-140419
```

## Persian and RTL Notes

- The UI language is English
- Excel column names can be Persian
- Generated PDF content can be Persian
- RTL shaping is available per box and is disabled by default
- For proper Persian rendering, add a suitable font such as `Vazirmatn-Regular.ttf` to `assets/fonts/`

If no custom Persian-capable font is available, rendering depends on the fallback font and may not look correct for all characters.

## Project Structure

```text
pdf-excel-filler/
├── main.py
├── requirements.txt
├── PDFExcelFiller.spec
├── README.md
├── app/
│   ├── core/
│   ├── models/
│   └── ui/
├── assets/
│   ├── fonts/
│   └── icons/
├── output/
├── samples/
├── templates/
└── tests/
```

## Requirements

- Windows
- Python 3.13
- A local virtual environment at `.venv`

## Installation

Install all dependencies into the project-local virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run From Source

```powershell
.\.venv\Scripts\python.exe main.py
```

## Build Windows EXE

Recommended build command:

```powershell
.\.venv\Scripts\pyinstaller.exe PDFExcelFiller.spec
```

This generates:

```text
dist/PDFExcelFiller.exe
```

The spec file includes:

- the executable name
- the application icon
- packaged `assets/`
- windowed mode for desktop use

## AES-Encrypted PDF Support

Some PDFs can open normally in Windows or in the app preview, but still require AES support during output generation.

This happens because:

- PDF preview uses `PyMuPDF`
- output generation uses `pypdf`

If a PDF uses AES internally, `pypdf` requires `cryptography>=3.1`.

That dependency is included in `requirements.txt` and must be present before building the `.exe`.

## Sample Files

The `samples/` folder includes test assets:

- `samples/test_template.pdf`
- `samples/test_data.xlsx`
- `samples/test_template_aes.pdf`
- `samples/test_template_openable_aes.pdf`

Notes:

- `test_data.xlsx` contains 150 rows for testing output generation and loading behavior
- `test_template_aes.pdf` is an AES-encrypted PDF test file
- `test_template_openable_aes.pdf` is an AES-based scenario that can still appear openable in viewers, but exercises the `pypdf` AES dependency path

## Testing

Run the test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Known Packaging Notes

- If you update dependencies, rebuild the `.exe`
- If you change icons or bundled assets, rebuild the `.exe`
- The packaged app depends on files bundled through `PDFExcelFiller.spec`
