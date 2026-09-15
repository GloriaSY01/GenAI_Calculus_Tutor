"""Recover source-page previews from local PDFs, without inventing figure crops.

Requires pypdfium2. Run: python -m scripts.restore_textbook_pages --chapters 1
Only pages recorded in figures.json are rendered. No embedding rebuild needed.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "textbook" / "mit-calculus"


def restore(chapters):
    import pypdfium2 as pdfium

    figures = json.loads((ROOT / "figures.json").read_text(encoding="utf-8"))
    manifest = ROOT / "source_pages.json"
    records = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    for chapter in chapters:
        pages = sorted({int(f["pdf_page"]) for f in figures.values() if int(f["chapter"]) == chapter})
        with pdfium.PdfDocument(str(ROOT / "pdfs" / f"chapter_{chapter:02d}.pdf")) as pdf:
            for page_number in pages:
                if not 1 <= page_number <= len(pdf):
                    raise ValueError(f"Invalid PDF page: chapter {chapter}, page {page_number}")
                relative = f"recovered-pages/chapter-{chapter:02d}/page-{page_number:03d}.png"
                output = ROOT / "parsed" / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                page = pdf[page_number - 1]
                bitmap = page.render(scale=1.5)
                bitmap.to_pil().save(output)
                bitmap.close()
                page.close()
                records[f"source-page-{chapter}-{page_number}"] = {
                    "chapter": chapter, "pdf_page": page_number, "path": relative,
                }
        print(f"Chapter {chapter}: {len(pages)} source pages restored", flush=True)
    temporary = manifest.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
    temporary.replace(manifest)
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapters", nargs="+", type=int, choices=range(1, 9), default=[1])
    restore(parser.parse_args().chapters)
