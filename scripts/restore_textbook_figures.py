"""Recreate reviewed independent figure crops from original local PDFs.
Requires pypdfium2. Run: python -m scripts.restore_textbook_figures
Only explicitly reviewed rectangles in figure_crops.json are extracted.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "textbook" / "mit-calculus"


def restore():
    import pypdfium2 as pdfium
    figures = json.loads((ROOT / "figures.json").read_text(encoding="utf-8"))
    recipes = json.loads((ROOT / "figure_crops.json").read_text(encoding="utf-8"))
    for key, recipe in recipes.items():
        if not recipe.get("reviewed"):
            continue
        figure = figures[key]
        left, top, right, bottom = recipe["bbox_fraction"]
        if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
            raise ValueError(f"Invalid crop: {key}")
        with pdfium.PdfDocument(str(ROOT / "pdfs" / f"chapter_{int(figure['chapter']):02d}.pdf")) as pdf:
            page = pdf[int(figure["pdf_page"]) - 1]
            bitmap = page.render(scale=3)
            image = bitmap.to_pil()
            crop = image.crop((round(left * image.width), round(top * image.height),
                               round(right * image.width), round(bottom * image.height)))
            target = ROOT / figure["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            crop.save(target)
            bitmap.close()
            page.close()
        print(f"Restored {key}")


if __name__ == "__main__":
    restore()
