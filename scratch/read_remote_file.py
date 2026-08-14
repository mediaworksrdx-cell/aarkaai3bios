import os
path = '/home/ubuntu/aarkaai3b/workspace/previous_message.txt'
if os.path.exists(path):
    print("File exists, size:", os.path.getsize(path))
    with open(path, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("File does not exist")
