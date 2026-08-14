import base64
from weasyprint import HTML
import os

# Create a tiny 1x1 red PNG
png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82'
b64_str = "data:image/png;base64," + base64.b64encode(png_bytes).decode('utf-8')

html = f"""<html>
<body>
<h1>Hello World</h1>
<img src="{b64_str}" style="width: 100px; height: 100px; display: block;">
</body>
</html>"""

HTML(string=html).write_pdf('/workspace/aarkaai3b/workspace/tiny_test.pdf')
print("Tiny PDF size:", os.path.getsize('/workspace/aarkaai3b/workspace/tiny_test.pdf'))

import pdfplumber
with pdfplumber.open('/workspace/aarkaai3b/workspace/tiny_test.pdf') as pdf:
    print("Pages:", len(pdf.pages))
    print("Images on Page 1:", len(pdf.pages[0].images))
