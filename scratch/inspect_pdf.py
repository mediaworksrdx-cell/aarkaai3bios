import pdfplumber
import sys

def inspect(filename):
    print(f"=== Inspecting {filename} ===")
    with pdfplumber.open(filename) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"--- Page {i+1} ---")
            print(text if text else "[EMPTY PAGE]")
            print(f"Images count: {len(page.images)}")
            print(f"Tables count: {len(page.extract_tables())}")
            print("-" * 20)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect(sys.argv[1])
    else:
        inspect("test_out_previous_message.pdf")
