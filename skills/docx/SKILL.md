---
name: docx
description: >
  Use this skill for anything involving Word documents (.docx) — creating,
  reading, editing, formatting, adding tables, images, headers/footers, styles,
  or converting content into a Word file. Trigger whenever the user mentions
  Word, .docx, a report, memo, letter, or any professional document deliverable.
---

# DOCX Skill

Use **python-docx** for all Word document tasks.

## Installation
```bash
pip install python-docx
```

---

## 1. Creating a Document

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches

doc = Document()

# Title
title = doc.add_heading("Document Title", level=0)

# Paragraph
p = doc.add_paragraph("This is a normal paragraph.")

# Bold / italic inline
p = doc.add_paragraph()
run = p.add_run("Bold text ")
run.bold = True
run2 = p.add_run("and italic.")
run2.italic = True

doc.save("output.docx")
```

---

## 2. Headings & Structure

```python
doc.add_heading("Section 1", level=1)
doc.add_heading("Subsection 1.1", level=2)
doc.add_paragraph("Content here.")
```

Heading levels: 0 = Title, 1 = H1, 2 = H2, 3 = H3

---

## 3. Tables

```python
table = doc.add_table(rows=1, cols=3)
table.style = "Table Grid"

# Header row
hdr = table.rows[0].cells
hdr[0].text = "Name"
hdr[1].text = "Age"
hdr[2].text = "City"

# Data rows
data = [("Alice", "30", "Chennai"), ("Bob", "25", "Mumbai")]
for name, age, city in data:
    row = table.add_row().cells
    row[0].text = name
    row[1].text = age
    row[2].text = city
```

---

## 4. Font & Paragraph Styling

```python
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

p = doc.add_paragraph("Styled text")
run = p.runs[0]
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)  # dark blue

p.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

---

## 5. Page Layout

```python
from docx.shared import Inches
from docx.oxml.ns import qn
import docx.oxml

section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.left_margin = Inches(1)
section.right_margin = Inches(1)
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
```

---

## 6. Headers & Footers

```python
section = doc.sections[0]

# Header
header = section.header
header.paragraphs[0].text = "My Company | Confidential"

# Footer with page number
footer = section.footer
footer.paragraphs[0].text = "Page "
run = footer.paragraphs[0].add_run()
# Add auto page number field
fldChar = docx.oxml.OxmlElement("w:fldChar")
fldChar.set(qn("w:fldCharType"), "begin")
run._r.append(fldChar)
instrText = docx.oxml.OxmlElement("w:instrText")
instrText.text = "PAGE"
run._r.append(instrText)
fldChar2 = docx.oxml.OxmlElement("w:fldChar")
fldChar2.set(qn("w:fldCharType"), "end")
run._r.append(fldChar2)
```

---

## 7. Inserting Images

```python
doc.add_picture("image.png", width=Inches(4))
```

---

## 8. Reading an Existing Document

```python
doc = Document("existing.docx")

# All text
for para in doc.paragraphs:
    print(para.style.name, ":", para.text)

# Tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text, end="\t")
        print()
```

---

## 9. Bullet & Numbered Lists

```python
# Bullet list
doc.add_paragraph("First item", style="List Bullet")
doc.add_paragraph("Second item", style="List Bullet")

# Numbered list
doc.add_paragraph("Step one", style="List Number")
doc.add_paragraph("Step two", style="List Number")
```

---

## Output

Always end with:
```python
doc.save("output.docx")
```

Use descriptive filenames. Default output path: current directory.
