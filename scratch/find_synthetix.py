import os
downloads_dir = r"C:\Users\daarv\Downloads"
if os.path.exists(downloads_dir):
    print("Files in Downloads matching 'synth':")
    for f in os.listdir(downloads_dir):
        if "synth" in f.lower():
            print(f)
else:
    print("Downloads dir does not exist")
