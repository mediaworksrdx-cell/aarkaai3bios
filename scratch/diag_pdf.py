#!/usr/bin/env python3
"""Diagnostic: generate a test PDF and report chart/image sizes."""
import sys, os, time
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s")

from pathlib import Path
from config import SAFE_WORK_DIR

print("=" * 60)
print("DIAGNOSTIC: PDF Chart & Image Generation")
print("=" * 60)

# 1. Check matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    print(f"[OK] matplotlib {matplotlib.__version__} available")
except ImportError as e:
    print(f"[FAIL] matplotlib: {e}")

# 2. Check torch + diffusers
try:
    import torch
    print(f"[OK] torch {torch.__version__}, CUDA={torch.cuda.is_available()}")
except ImportError as e:
    print(f"[FAIL] torch: {e}")

try:
    import diffusers
    print(f"[OK] diffusers {diffusers.__version__}")
except ImportError as e:
    print(f"[FAIL] diffusers: {e}")

# 3. Check aarkaa-vision-standalone model
model_path = "/workspace/aarkaai3b/aarkaa-vision-standalone"
if os.path.exists(model_path):
    files = os.listdir(model_path)
    print(f"[OK] aarkaa-vision-standalone exists with {len(files)} entries: {files}")
    # Check for actual weight files
    for root, dirs, fnames in os.walk(model_path):
        for fname in fnames:
            fpath = os.path.join(root, fname)
            fsize = os.path.getsize(fpath)
            if fsize > 1_000_000:
                print(f"  [WEIGHT] {os.path.relpath(fpath, model_path)} = {fsize/1e6:.1f} MB")
else:
    print(f"[FAIL] aarkaa-vision-standalone not found at {model_path}")

# 4. Test chart generation (matplotlib PNG)
print("\n--- Testing matplotlib chart generation ---")
from modules.gamma_charts import get_chart_resource
charts_dir = Path(SAFE_WORK_DIR) / "charts"
charts_dir.mkdir(parents=True, exist_ok=True)

t0 = time.time()
chart = get_chart_resource(
    ['Q1', 'Q2', 'Q3', 'Q4'], [100, 250, 400, 600],
    'Test Revenue Growth', 'bar', '#6366F1', 'diag_chart', charts_dir
)
t1 = time.time()
print(f"  Chart type: {chart['type']}")
print(f"  URL length: {len(chart.get('url', ''))} chars")
print(f"  File path: {chart.get('file_path', 'N/A')}")
print(f"  Time: {t1-t0:.2f}s")
if chart.get('file_path') and os.path.exists(chart['file_path']):
    fsize = os.path.getsize(chart['file_path'])
    print(f"  File size: {fsize} bytes ({fsize/1024:.1f} KB)")

# 5. Test Aarka Vision image generation
print("\n--- Testing Aarka Vision image generation ---")
from modules.gamma_charts import get_aarkavision_image_resource

t0 = time.time()
try:
    img = get_aarkavision_image_resource(
        "modern corporate office, professional business setting, photorealistic, 8k",
        "diag_illustration", charts_dir
    )
    t1 = time.time()
    print(f"  Image type: {img['type']}")
    print(f"  URL length: {len(img.get('url', ''))} chars")
    print(f"  File path: {img.get('file_path', 'N/A')}")
    print(f"  Time: {t1-t0:.2f}s")
    if img.get('file_path') and os.path.exists(img['file_path']):
        fsize = os.path.getsize(img['file_path'])
        print(f"  File size: {fsize} bytes ({fsize/1024:.1f} KB)")
except Exception as e:
    t1 = time.time()
    print(f"  [FAIL] Aarka Vision failed in {t1-t0:.2f}s: {e}")
    import traceback
    traceback.print_exc()

# 6. Test full PDF compilation
print("\n--- Testing full PDF compilation ---")
from modules.gamma_pdf import compile_gamma_pdf

t0 = time.time()
try:
    pdf_path = compile_gamma_pdf("AI Technology Startups", "diag_test_output.pdf")
    t1 = time.time()
    print(f"  PDF path: {pdf_path}")
    if os.path.exists(pdf_path):
        fsize = os.path.getsize(pdf_path)
        print(f"  PDF size: {fsize} bytes ({fsize/1024:.1f} KB)")
        if fsize < 100_000:
            print(f"  [WARNING] PDF is suspiciously small ({fsize/1024:.1f} KB). Charts/images may have failed.")
        else:
            print(f"  [OK] PDF size looks healthy.")
    print(f"  Time: {t1-t0:.2f}s")
except Exception as e:
    t1 = time.time()
    print(f"  [FAIL] PDF compilation failed in {t1-t0:.2f}s: {e}")
    import traceback
    traceback.print_exc()

# 7. Check generated HTML for base64 content
print("\n--- Checking debug HTML for embedded images ---")
html_path = Path(SAFE_WORK_DIR) / "diag_test_output.html"
if html_path.exists():
    html_content = html_path.read_text(encoding='utf-8')
    b64_count = html_content.count('data:image/png;base64,')
    svg_count = html_content.count('<svg ')
    img_count = html_content.count('<img ')
    print(f"  HTML size: {len(html_content)} chars")
    print(f"  Base64 PNG images: {b64_count}")
    print(f"  Inline SVGs: {svg_count}")
    print(f"  <img> tags: {img_count}")
else:
    print(f"  [FAIL] Debug HTML not found at {html_path}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
