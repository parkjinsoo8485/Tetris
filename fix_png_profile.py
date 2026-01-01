from PIL import Image
import os

TARGET_DIRS = [
    "assets/blocks",
    # 필요하면 여기 추가
    # "assets/ui",
    # "assets/backgrounds",
]

def clean_png(path):
    img = Image.open(path)
    img = img.convert("RGBA")   # 색상 프로파일 제거 핵심
    img.save(path, optimize=True)

for folder in TARGET_DIRS:
    if not os.path.exists(folder):
        continue

    for name in os.listdir(folder):
        if name.lower().endswith(".png"):
            path = os.path.join(folder, name)
            clean_png(path)
            print(f"cleaned: {path}")
