import sys
import os
sys.path.append(os.getcwd())

# Mock chromadb and other heavy database modules not present on local windows environment
from unittest.mock import MagicMock
sys.modules['chromadb'] = MagicMock()
sys.modules['modules.rag'] = MagicMock()

import logging
logging.basicConfig(level=logging.INFO)

from modules.gamma_pdf import compile_gamma_pdf

def main():
    print("Compiling Chennai Tech Startups premium report directly...")
    try:
        pdf_path = compile_gamma_pdf("Chennai Tech Startups", "chennai_tech_startups_premium_v5.pdf")
        print(f"Success! PDF generated at: {pdf_path}")
    except Exception as e:
        print(f"Error during compilation: {e}")

if __name__ == "__main__":
    main()
