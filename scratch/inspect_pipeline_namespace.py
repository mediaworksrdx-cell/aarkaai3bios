import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import pipeline
print("Pipeline File:", pipeline.__file__)
# See what is inside pipeline namespace
print("Pipeline contents:")
for name in sorted(dir(pipeline)):
    val = getattr(pipeline, name)
    print(f"  {name}: {type(val)}")
