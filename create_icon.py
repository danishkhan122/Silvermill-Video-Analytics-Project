"""
Create SilverMill.ico from the app logo for use as the desktop shortcut icon.
Run this once (or use "Create Desktop Shortcut.bat") to generate the icon.
If Pillow is installed and static/images/logo.png exists, that image is used.
Otherwise a simple fallback icon is created (no Pillow needed).
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "static", "images", "logo.png")
ICO_PATH = os.path.join(SCRIPT_DIR, "SilverMill.ico")


def create_ico_from_pillow():
    """Create .ico from logo.png using Pillow."""
    try:
        from PIL import Image
    except ImportError:
        return False
    if not os.path.isfile(LOGO_PATH):
        return False
    try:
        img = Image.open(LOGO_PATH)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        img.save(ICO_PATH, format="ICO", sizes=sizes)
        print("Icon created from logo: SilverMill.ico")
        return True
    except Exception as e:
        print("Could not create icon from logo:", e)
        return False


def create_fallback_ico():
    """Create a minimal 32x32 .ico file without Pillow (simple colored square)."""
    # Minimal ICO: 6-byte header + 16-byte dir entry + 40-byte BMP header + 32*32*4 pixel data
    header = bytes([
        0, 0, 1, 0, 1, 0,   # 1 image
    ])
    width, height = 32, 32
    bpp = 32
    row = (width * 4 + 3) & ~3
    size_img = 40 + row * height
    offset = 6 + 16
    dir_entry = bytes([
        width, height, 0, 0, 1, 0, bpp, 0,
        size_img & 0xFF, (size_img >> 8) & 0xFF, (size_img >> 16) & 0xFF, (size_img >> 24) & 0xFF,
        offset & 0xFF, (offset >> 8) & 0xFF, (offset >> 16) & 0xFF, (offset >> 24) & 0xFF,
    ])
    bmp_header = bytes([
        40, 0, 0, 0, width, 0, 0, 0, height * 2, 0, 0, 0, 1, 0, bpp, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    ])
    # Purple/blue gradient-ish pixels (32x32 BGRA, bottom-up)
    pixels = bytearray()
    for y in range(height - 1, -1, -1):
        for x in range(width):
            # Simple purple (#6a11cb style)
            r, g, b = 0x6a, 0x11, 0xcb
            a = 255
            pixels.extend([b, g, r, a])
        pad = row - width * 4
        pixels.extend([0] * pad)
    try:
        with open(ICO_PATH, "wb") as f:
            f.write(header)
            f.write(dir_entry)
            f.write(bmp_header)
            f.write(pixels)
        print("Fallback icon created: SilverMill.ico")
        return True
    except Exception as e:
        print("Could not write fallback icon:", e)
        return False


def main():
    os.chdir(SCRIPT_DIR)
    if create_ico_from_pillow():
        return 0
    if create_fallback_ico():
        return 0
    print("No icon created. Install Pillow and add static/images/logo.png for logo-based icon.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
