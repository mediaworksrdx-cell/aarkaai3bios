import os
from PIL import Image

# Configuration
SOURCE_IMAGE = r"C:\Users\daarv\.gemini\antigravity\brain\ea5784cb-1edc-424d-b63f-3406ef7cfd16\final_sunrise_icon_no_text_1776148804664.png"
ANDROID_RES_DIR = "android-app/app/src/main/res"
IOS_ASSET_DIR = "ios-app/AarkaaiApp/Assets.xcassets/AppIcon.appiconset"

# Android Sizes (Legacy)
ANDROID_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192
}

# iOS Sizes (Simplified set for typical iPhone project)
IOS_SIZES = [
    (20, "20x20@1x"), (40, "20x20@2x"), (60, "20x20@3x"),
    (29, "29x29@1x"), (58, "29x29@2x"), (87, "29x29@3x"),
    (40, "40x40@1x"), (80, "40x40@2x"), (120, "40x40@3x"),
    (120, "60x60@2x"), (180, "60x60@3x"),
    (1024, "1024x1024@1x")
]

def process_icons():
    if not os.path.exists(SOURCE_IMAGE):
        print(f"Error: Source image not found at {SOURCE_IMAGE}")
        return

    img = Image.open(SOURCE_IMAGE)

    # 1. Process Android Icons
    print("Generating Android Icons...")
    for folder, size in ANDROID_SIZES.items():
        path = os.path.join(ANDROID_RES_DIR, folder)
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, "ic_launcher.png")
        # For Android round icons, we'll use the same for now
        filename_round = os.path.join(path, "ic_launcher_round.png")
        
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(filename)
        resized.save(filename_round)
        print(f"  - Saved to {folder}")

    # 2. Process iOS Icons
    print("Generating iOS Icons...")
    os.makedirs(IOS_ASSET_DIR, exist_ok=True)
    
    contents_json = {
        "images": [],
        "info": {"version": 1, "author": "xcode"}
    }
    
    for size_px, name in IOS_SIZES:
        filename = f"Icon-{name}.png"
        full_path = os.path.join(IOS_ASSET_DIR, filename)
        
        resized = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
        resized.save(full_path)
        
        # Parse idiom and scale from name
        # e.g. 20x20@2x -> size 20, scale 2x
        parts = name.split("@")
        size_str = parts[0]
        scale_str = parts[1]
        
        contents_json["images"].append({
            "size": size_str,
            "idiom": "iphone",
            "filename": filename,
            "scale": scale_str
        })
        print(f"  - Saved {filename}")

    # Add iPad variants (copy from iPhone for simplicity)
    for size_px, name in IOS_SIZES:
        if size_px <= 180: # Filter typical iPad sizes
             parts = name.split("@")
             contents_json["images"].append({
                "size": parts[0],
                "idiom": "ipad",
                "filename": f"Icon-{name}.png",
                "scale": parts[1]
            })

    # Save Contents.json
    import json
    with open(os.path.join(IOS_ASSET_DIR, "Contents.json"), "w") as f:
        json.dump(contents_json, f, indent=2)
    print("  - Generated Contents.json")

if __name__ == "__main__":
    process_icons()
