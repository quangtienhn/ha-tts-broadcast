"""Generate brand PNGs for the TTS Broadcast integration."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "custom_components" / "tts_broadcast" / "brand"
SIZES = {
    "icon.png": 256,
    "icon@2x.png": 512,
    "dark_icon.png": 256,
    "dark_icon@2x.png": 512,
}


def draw(size: int, dark: bool) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (255, 255, 255, 255) if dark else (31, 111, 235, 255)
    s = size / 256
    # Speaker body
    d.rectangle((72 * s, 96 * s, 88 * s, 160 * s), fill=color)
    points = [
        (88 * s, 96 * s),
        (128 * s, 64 * s),
        (128 * s, 192 * s),
        (88 * s, 160 * s),
    ]
    d.polygon(points, fill=color)
    # Waves
    for x0, x1, y_top, y_bot in ((132, 142, 92, 164), (156, 166, 76, 180)):
        d.arc(
            (x0 * s, y_top * s, x1 * s + 20 * s, y_bot * s),
            start=-60,
            end=60,
            fill=color,
            width=int(10 * s),
        )
    # Dots
    for cx, cy in ((196, 96), (212, 128), (196, 160)):
        d.ellipse(
            (cx * s - 8 * s, cy * s - 8 * s, cx * s + 8 * s, cy * s + 8 * s),
            fill=color,
        )
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size in SIZES.items():
        dark = name.startswith("dark_")
        draw(size, dark).save(OUT / name)
        print(f"wrote {OUT / name}")


if __name__ == "__main__":
    main()