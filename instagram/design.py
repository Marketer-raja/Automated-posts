import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ART = Path(__file__).with_name("art")
TEMPLATES = [("cover", 426, 777), ("change", 475, 620),
             ("impact", 475, 620), ("action", 439, 732)]
FONT = os.environ.get("CAROUSEL_FONT", "DejaVuSans-Bold.ttf")


def headline(draw, words):
    for size in range(132, 37, -2):
        font = ImageFont.truetype(FONT, size)
        lines = [""]
        for word in words.split():
            line = (lines[-1] + " " + word).strip()
            if lines[-1] and draw.textlength(line, font=font) > 934:
                lines.append(word)
            else:
                lines[-1] = line
        if max(draw.textlength(line, font=font) for line in lines) > 934:
            continue
        if len(lines) * size * 1.12 > 420:
            continue
        draw.multiline_text((540, 385), "\n".join(lines), font=font, fill="white",
                            align="center", anchor="mm", spacing=6, stroke_width=0)
        return
    raise ValueError("Slide headline is too long to fit")


def render(slides, output):
    output.mkdir(parents=True, exist_ok=True)
    for index, ((name, top, bottom), copy) in enumerate(zip(TEMPLATES, slides, strict=True), 1):
        with Image.open(ART / f"{name}.jpg") as source:
            canvas = Image.new("RGB", (736, 920), (183, 2, 29))
            # Feather the red edges into a solid field without stretching character shadows.
            band = source.crop((0, top, 736, bottom))
            canvas.paste(band, (0, top))
            for edge, y, direction in [(0, top-1, -1), (band.height-1, bottom, 1)]:
                strip = band.crop((0, edge, 736, edge+1))
                field = Image.new("RGB", strip.size, (183, 2, 29))
                for offset in range(32):
                    blurred = strip.filter(ImageFilter.GaussianBlur(offset / 3))
                    tint = Image.blend(blurred, field, (offset+1)/32)
                    canvas.paste(tint, (0, y + offset*direction))
        canvas = canvas.resize((1080, 1350), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(canvas)
        draw.text((65, 65), "MARKETER RAJA", font=ImageFont.truetype(FONT, 34), fill="white")
        headline(draw, copy)
        draw.text((540, 1260), f"{index} / 4", anchor="mm",
                  font=ImageFont.truetype(FONT, 27), fill="white")
        canvas.save(output / f"{index:02d}.jpg", quality=93, optimize=True)
