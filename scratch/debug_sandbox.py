import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from pipeline import _extract_python_code, _execute_python_code

query = """What is the output?

def test():
    x = [1, 2, 3]
    y = x
    y.append(4)
    print(x)

test()"""

code = _extract_python_code(query)
print("Extracted Code:")
print(repr(code))

print("\nExecuting Code:")
out = _execute_python_code(code)
print("Execution Result:")
print(repr(out))
