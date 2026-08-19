"""Renders a sample GST certificate image for the OCR demo step
(Onboarding's document upload), matching docs/sample_gst_certificate.tex's
content/design without needing a LaTeX toolchain (none is installed here).

Run from the backend/ directory:
    python -m seed.create_demo_persona_assets

Output: docs/demo_assets/sample_gst_certificate.png. Clearly labeled as a
fabricated sample, same as the .tex source -- not a real government record
(CLAUDE.md rule 3).

Sized for OCR accuracy over speed: a smaller/downscaled render was tried
to cut CPU inference time, but EasyOCR's internal canvas_size means input
resolution barely affects wall-clock time (readtext still took ~37s) while
meaningfully hurting recognition accuracy (GSTIN extraction failed on the
smaller render, succeeded on this one). ~40s of real local CPU inference
is an accurate expectation to set before a live demo, not a bug.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs" / "demo_assets"
OUTPUT_PATH = OUTPUT_DIR / "sample_gst_certificate.png"

WIDTH, HEIGHT = 1240, 1050
GOV_BLUE = (20, 60, 120)
SAMPLE_GRAY = (140, 140, 140)
BLACK = (20, 20, 20)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
    except OSError:
        return ImageFont.load_default()


def render_sample_certificate() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), color="white")
    draw = ImageDraw.Draw(img)
    margin = 70
    y = 40

    draw.text((WIDTH / 2, y), "SAMPLE DOCUMENT — FOR DEMONSTRATION PURPOSES ONLY", fill=SAMPLE_GRAY, font=_font(24, True), anchor="mm")
    y += 34
    draw.text((WIDTH / 2, y), "This is not an official government record and has no legal validity.", fill=SAMPLE_GRAY, font=_font(16), anchor="mm")
    y += 40
    draw.line([(margin, y), (WIDTH - margin, y)], fill=BLACK, width=2)
    y += 40

    draw.text((WIDTH / 2, y), "Goods and Services Tax", fill=GOV_BLUE, font=_font(40, True), anchor="mm")
    y += 50
    draw.text((WIDTH / 2, y), "Registration Certificate", fill=GOV_BLUE, font=_font(32, True), anchor="mm")
    y += 36
    draw.text((WIDTH / 2, y), "Form GST REG-06 (specimen layout)", fill=BLACK, font=_font(16), anchor="mm")
    y += 30
    draw.line([(margin, y), (WIDTH - margin, y)], fill=BLACK, width=2)
    y += 50

    rows = [
        ("GSTIN", "27AASCD1234F1Z5"),
        ("Legal Name", "Ganga Textiles Private Limited"),
        ("Trade Name", "Ganga Textiles"),
        ("Constitution of Business", "Private Limited Company"),
        ("Date of Registration", "01/06/2018"),
        ("Registered Address", "Plot No. 14, Industrial Estate, Coimbatore, Tamil Nadu - 641021"),
        ("Jurisdiction", "State - Tamil Nadu, Ward 12"),
        ("Type of Registration", "Regular"),
        ("Status", "Active"),
    ]
    label_font = _font(22, True)
    value_font = _font(22)
    for label, value in rows:
        draw.text((margin, y), label, fill=BLACK, font=label_font)
        draw.text((margin + 320, y), value, fill=BLACK, font=value_font)
        y += 48

    y += 20
    draw.line([(margin, y), (WIDTH - margin, y)], fill=(180, 180, 180), width=1)
    y += 30
    draw.text((margin, y), "This certificate is system-generated and does not require a physical signature.", fill=BLACK, font=_font(15))
    draw.text((WIDTH - margin, y), "Digitally signed", fill=BLACK, font=_font(15), anchor="ra")
    draw.text((WIDTH - margin, y + 20), "Jurisdictional Authority", fill=BLACK, font=_font(15), anchor="ra")
    draw.text((WIDTH - margin, y + 40), "Date: 01/06/2018", fill=BLACK, font=_font(15), anchor="ra")

    y = HEIGHT - 50
    draw.text(
        (WIDTH / 2, y),
        "Generated for the AI-Powered MSME Compliance Assistant prototype (SIH 2026) - upload-and-extract demo only.",
        fill=SAMPLE_GRAY,
        font=_font(14),
        anchor="mm",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = render_sample_certificate()
    print(f"Wrote {path}")
