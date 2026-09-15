"""Extract embedded illustrations at their PDF bounds, preserving chapter/page.
Requires pypdfium2 and Pillow. No OCR, model calls or whole-page output.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "textbook" / "mit-calculus"


def extract(chapters):
    import pypdfium2 as pdfium
    from PIL import Image, ImageOps, ImageDraw
    manifest = ROOT / "extracted_figures.json"
    records = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    for chapter in chapters:
        records = {k: v for k, v in records.items() if v["chapter"] != chapter}
        thumbnails = []
        with pdfium.PdfDocument(str(ROOT / "pdfs" / f"chapter_{chapter:02d}.pdf")) as pdf:
            for page_index in range(len(pdf)):
                page = pdf[page_index]
                width, height = page.get_size()
                objects = sorted((obj for obj in page.get_objects() if obj.type == 3),
                                 key=lambda obj: (-obj.get_bounds()[3], obj.get_bounds()[0]))
                if not objects:
                    page.close()
                    continue
                textpage = page.get_textpage()
                bitmap = page.render(scale=3)
                rendered = bitmap.to_pil()
                for index, obj in enumerate(objects):
                    left, bottom, right, top = obj.get_bounds()
                    if right - left < 30 or top - bottom < 20:
                        continue
                    key = f"pdf-figure-{chapter}-{page_index + 1}-{index + 1}"
                    raw_caption = textpage.get_text_bounded(max(0, left - 30), max(0, bottom - 24), min(width, right + 30), bottom)
                    match = re.match(r"\s*Fig(?:ure)?\.?\s*(\d+\.\d+)", raw_caption)
                    number = f"Figure {match.group(1)}" if match else ""
                    path = f"parsed/extracted/ch{chapter:02d}/{key}.png"
                    crop = rendered.crop((round(left * 3), round((height - top) * 3),
                                          round(right * 3), round((height - bottom) * 3)))
                    target = ROOT / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    crop.save(target)
                    records[key] = {
                        "path": path, "chapter": chapter, "pdf_page": page_index + 1,
                        "figure_number": number, "caption": "", "caption_text_raw": raw_caption,
                        "extraction": "pdf_image_bounds", "bbox_pdf": [left, bottom, right, top],
                    }
                    tile = Image.new("RGB", (310, 205), "white")
                    preview = ImageOps.contain(crop.convert("RGB"), (300, 174))
                    tile.paste(preview, ((310-preview.width)//2, 24))
                    ImageDraw.Draw(tile).text((5, 5), f"p{page_index+1} #{index+1} {number}", fill="black")
                    thumbnails.append(tile)
                textpage.close()
                bitmap.close()
                page.close()
        sheet = Image.new("RGB", (310 * 4, 205 * ((len(thumbnails)+3)//4)), "#dddddd")
        for index, tile in enumerate(thumbnails):
            sheet.paste(tile, ((index % 4)*310, (index//4)*205))
        output = ROOT.parents[2] / "tmp" / "figure-review"
        output.mkdir(parents=True, exist_ok=True)
        sheet.save(output / f"chapter-{chapter:02d}.png")
        print(f"Chapter {chapter}: {len(thumbnails)} independent illustrations", flush=True)
    manifest.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters", type=int, nargs="+", choices=range(1,9), default=list(range(1,9)))
    extract(parser.parse_args().chapters)
