---
name: file-reading
description: >
  Use this skill when the user uploads or provides a file path and wants its
  contents read, parsed, or analyzed. Covers all common file types: PDF, DOCX,
  XLSX, CSV, JSON, TXT, images, and archives. Use this skill to decide which
  tool or library to use for each file type before attempting to read it.
  Trigger whenever a file path or upload is mentioned and the content is not
  already in context.
---

# File Reading Skill

This skill is a router. Given a file, use the table below to pick the right
approach, then follow the instructions for that type.

---

## Quick Decision Table

| Extension | Method |
|---|---|
| `.pdf` | pdfplumber (text), pypdf (structure) → see pdf skill |
| `.docx` | python-docx → see docx skill |
| `.xlsx`, `.xls` | pandas.read_excel or openpyxl → see xlsx skill |
| `.csv` | pandas.read_csv |
| `.json` | json.load |
| `.txt`, `.md` | open().read() |
| `.png`, `.jpg`, `.jpeg`, `.webp` | Send as image to vision model |
| `.zip`, `.tar.gz` | Extract first, then route by contents |
| `.pptx` | python-pptx → see pptx skill |

---

## 1. CSV

```python
import pandas as pd

df = pd.read_csv("file.csv")
print(df.shape)
print(df.head())
print(df.dtypes)
```

For encoding issues:
```python
df = pd.read_csv("file.csv", encoding="latin-1")
```

---

## 2. JSON

```python
import json

with open("file.json", "r") as f:
    data = json.load(f)

# If it's a list
if isinstance(data, list):
    print(f"{len(data)} records")
    print(data[0])

# If it's a dict
if isinstance(data, dict):
    print(list(data.keys()))
```

---

## 3. Plain Text / Markdown

```python
with open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()

print(content[:500])  # preview first 500 chars
```

---

## 4. Images (Vision)

If your LLM supports vision, encode the image as base64:

```python
import base64

with open("image.png", "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

# Pass to model as:
# {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}
```

---

## 5. Archives (ZIP / TAR)

```python
import zipfile
import os

with zipfile.ZipFile("archive.zip", "r") as z:
    print(z.namelist())       # list contents
    z.extractall("./extracted")

# Then route each extracted file through this skill again
```

For .tar.gz:
```python
import tarfile

with tarfile.open("archive.tar.gz", "r:gz") as tar:
    print(tar.getnames())
    tar.extractall("./extracted")
```

---

## 6. Detecting File Type Automatically

```python
import mimetypes

mime_type, _ = mimetypes.guess_type("unknown_file")
print(mime_type)
# e.g. "application/pdf", "text/csv", "image/png"
```

Or by extension:
```python
from pathlib import Path

ext = Path("myfile.xlsx").suffix.lower()
# ext = ".xlsx"
```

---

## Strategy for Unknown Files

1. Check the extension first
2. If ambiguous, read the first few bytes (magic bytes):
   - PDF: starts with `%PDF`
   - ZIP: starts with `PK`
   - XLSX (also a ZIP): extract and look for `xl/` folder
3. If it's a text file with unknown extension, try `open().read()` with UTF-8
4. If binary and unrecognized, tell the user you can't parse it

---

## After Reading

Once you've read the file, always:
1. Report what you found (shape, length, keys, page count, etc.)
2. Ask or infer what the user wants to do with it
3. Use the appropriate domain skill if needed (pdf, xlsx, docx, etc.)
