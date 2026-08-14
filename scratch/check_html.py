import os
html = open('/workspace/aarkaai3b/workspace/chennai_tech_startups.html', 'r', encoding='utf-8').read()
print(f"HTML size: {len(html)} chars")
print(f"Base64 PNGs: {html.count('data:image/png;base64,')}")
print(f"Inline SVGs: {html.count('<svg ')}")
print(f"img tags: {html.count('<img ')}")
print(f"illustration-img: {html.count('illustration-img')}")
print(f"chart-img: {html.count('chart-img')}")
print(f"page divs: {html.count('class=\"page\"')}")

pdf_path = '/workspace/aarkaai3b/workspace/chennai_tech_startups.pdf'
print(f"\nPDF size: {os.path.getsize(pdf_path)} bytes ({os.path.getsize(pdf_path)/1024:.1f} KB)")

# Check chart image sizes
charts_dir = '/workspace/aarkaai3b/workspace/charts'
for f in sorted(os.listdir(charts_dir)):
    fp = os.path.join(charts_dir, f)
    print(f"  {f}: {os.path.getsize(fp)} bytes ({os.path.getsize(fp)/1024:.1f} KB)")

# Check first 200 chars of each base64 img src to see if they look valid
import re
imgs = re.findall(r'<img[^>]*src="(data:image/png;base64,[A-Za-z0-9+/=]{0,100})', html)
print(f"\nFound {len(imgs)} base64 img tags")
for i, m in enumerate(imgs):
    print(f"  img{i+1}: {m[:80]}...")
