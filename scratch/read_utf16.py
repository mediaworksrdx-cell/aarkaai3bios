import os
import sys

# Set stdout encoding to utf-8 if possible
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

for filename in ['test_results.txt', 'test_out.txt']:
    if os.path.exists(filename):
        print(f"=== {filename} ===")
        try:
            with open(filename, 'rb') as f:
                raw = f.read()
            # Decode utf-16
            content = raw.decode('utf-16', errors='replace')
            # Print safely (replacing characters that can't be printed in the terminal)
            print(content[:3000].encode('ascii', errors='replace').decode('ascii'))
        except Exception as e:
            print(f"Error reading {filename}: {e}")
        print("="*40)
