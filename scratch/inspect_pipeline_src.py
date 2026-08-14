import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline
print("Pipeline File:", pipeline.__file__)
# Let's inspect process_query code lines 1020-1050
import inspect
src = inspect.getsource(pipeline.process_query)
lines = src.split('\n')
# Print line 30 to 70 of the process_query function
for idx, line in enumerate(lines[25:65]):
    print(f"{idx+26}: {line}")
