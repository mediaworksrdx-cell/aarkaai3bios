---
name: xlsx
description: >
  Use this skill for anything involving spreadsheets — creating, reading,
  editing, formatting Excel files (.xlsx), adding charts, formulas, conditional
  formatting, pivot-style summaries, or converting CSV/data to spreadsheets.
  Trigger whenever the user mentions Excel, .xlsx, spreadsheet, or tabular data
  that needs to be saved as a file.
---

# XLSX Skill

Use **openpyxl** for Excel file creation/editing, **pandas** for data
manipulation, and **xlsxwriter** for advanced charts.

## Installation
```bash
pip install openpyxl pandas xlsxwriter
```

---

## 1. Creating a Workbook

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"

# Write headers
headers = ["Name", "Age", "Score"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F497D")
    cell.alignment = Alignment(horizontal="center")

# Write data
data = [("Alice", 30, 92), ("Bob", 25, 87), ("Carol", 28, 95)]
for row_idx, row in enumerate(data, 2):
    for col_idx, val in enumerate(row, 1):
        ws.cell(row=row_idx, column=col_idx, value=val)

wb.save("output.xlsx")
```

---

## 2. Reading an Excel File

```python
import pandas as pd

df = pd.read_excel("input.xlsx", sheet_name="Sheet1")
print(df.head())

# All sheets
all_sheets = pd.read_excel("input.xlsx", sheet_name=None)
for name, df in all_sheets.items():
    print(f"Sheet: {name}")
    print(df)
```

---

## 3. Column Widths & Row Heights

```python
# Auto-fit column width
for col in ws.columns:
    max_len = max(len(str(cell.value or "")) for cell in col)
    ws.column_dimensions[get_column_letter(col[0].column)].width = max_len + 4

# Row height
ws.row_dimensions[1].height = 25
```

---

## 4. Formulas

```python
ws["D2"] = "=C2*1.1"          # formula in a cell
ws["D10"] = "=SUM(D2:D9)"     # sum
ws["E2"] = "=AVERAGE(C2:C9)"  # average
```

---

## 5. Conditional Formatting

```python
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.styles import PatternFill

# Color scale (green → red)
ws.conditional_formatting.add(
    "C2:C100",
    ColorScaleRule(
        start_type="min", start_color="63BE7B",
        end_type="max",   end_color="F8696B"
    )
)

# Highlight cells > 90
red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
ws.conditional_formatting.add(
    "C2:C100",
    CellIsRule(operator="greaterThan", formula=["90"], fill=red_fill)
)
```

---

## 6. Charts

```python
from openpyxl.chart import BarChart, Reference

chart = BarChart()
chart.title = "Scores"
chart.y_axis.title = "Score"
chart.x_axis.title = "Name"

data_ref = Reference(ws, min_col=3, min_row=1, max_row=4)
cats_ref = Reference(ws, min_col=1, min_row=2, max_row=4)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats_ref)

ws.add_chart(chart, "F2")
```

---

## 7. Multiple Sheets

```python
wb = Workbook()
ws1 = wb.active
ws1.title = "Summary"

ws2 = wb.create_sheet("Details")
ws3 = wb.create_sheet("Raw Data")
```

---

## 8. Freezing Panes & Filters

```python
ws.freeze_panes = "A2"          # freeze header row
ws.auto_filter.ref = ws.dimensions  # add dropdown filters
```

---

## 9. From CSV / pandas DataFrame

```python
import pandas as pd

df = pd.read_csv("data.csv")

# Clean up
df.columns = [c.strip() for c in df.columns]
df = df.dropna(how="all")

# Export to Excel with formatting via xlsxwriter
with pd.ExcelWriter("output.xlsx", engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="Data", index=False)
    workbook = writer.book
    worksheet = writer.sheets["Data"]

    header_fmt = workbook.add_format({"bold": True, "bg_color": "#1F497D", "font_color": "white"})
    for col_num, col_name in enumerate(df.columns):
        worksheet.write(0, col_num, col_name, header_fmt)
        worksheet.set_column(col_num, col_num, max(len(col_name) + 4, 12))
```

---

## Decision Guide

| Task | Tool |
|---|---|
| Create / edit .xlsx | openpyxl |
| Read data | pandas |
| Charts + advanced formatting | xlsxwriter |
| Quick CSV → Excel | pandas + xlsxwriter |
