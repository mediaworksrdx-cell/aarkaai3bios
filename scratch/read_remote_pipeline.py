with open('/home/ubuntu/aarkaai3b/pipeline.py', 'r', encoding='utf-8') as f:
    code = f.read()
    import re
    m = re.search(r'def _write_previous_message_file.*?(?=\n\n|\Z)', code, re.DOTALL)
    if m:
        print(m.group(0))
    else:
        print("Function not found!")
