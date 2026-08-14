import os
from bs4 import BeautifulSoup
import pdfplumber

html_path = '/workspace/aarkaai3b/workspace/chennai_tech_startups_test.html'
pdf_path = '/workspace/aarkaai3b/workspace/chennai_tech_startups_test.pdf'

print("=== CHECKING HTML ===")
if os.path.exists(html_path):
    print(f"HTML exists, size: {os.path.getsize(html_path)} bytes")
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    imgs = soup.find_all('img')
    print(f"Found {len(imgs)} img tags in HTML:")
    for i, img in enumerate(imgs):
        src = img.get('src', '')
        print(f"  Img {i+1}: class={img.get('class')}, src length={len(src)}, starts with={src[:50]}")
        
    svgs = soup.find_all('svg')
    print(f"Found {len(svgs)} svg tags in HTML")
else:
    print("HTML does not exist!")

print("\n=== CHECKING PDF ===")
if os.path.exists(pdf_path):
    print(f"PDF exists, size: {os.path.getsize(pdf_path)} bytes")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            print(f"  Page {i+1}: characters={len(text)}, images={len(page.images)}")
            if len(page.images) > 0:
                print(f"    Image details: {page.images}")
else:
    print("PDF does not exist!")
