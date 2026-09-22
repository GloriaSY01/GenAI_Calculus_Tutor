"""Populate textbook translations using the configured provider. No student data."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from backend import localization, textbook, rag

def main():
    root = Path(__file__).resolve().parents[1]
    catalog = textbook.catalog_tree()
    titles = ['Demo class', 'Calculus I · Class A', 'Calculus I · Class B']
    for c in catalog['chapters']:
        titles.append(c['title'])
        titles.extend(s['title'] for s in c['sections'])
    translated = localization.translate_texts(titles, 'zh')
    # Include titles without numeric prefixes for existing displayLabel callers.
    import re
    for key, value in list(translated.items()):
        translated[re.sub(r'^\d+(?:\.\d+)*\s+', '', key)] = re.sub(r'^\d+(?:\.\d+)*\s+', '', value)
    (root/'frontend-web/src/textbook-labels.json').write_text(json.dumps(translated, ensure_ascii=False, indent=2), encoding='utf-8')
    sections = [s for c in catalog['chapters'] for s in c['sections']]
    cards = {s['id']: rag.concept_card(s['title']) for s in sections}
    def translate_section(s):
        card = cards[s['id']]
        if hasattr(card, 'model_dump'): card=card.model_dump()
        texts = [card.get(k,'') for k in ['title','chapter','summary','definition','example','pitfalls']]
        for b in card.get('content',[]):
            texts.extend([b.get('heading',''), b.get('text','')])
            for f in b.get('figures',[]): texts.extend([f.get('caption',''),f.get('figure_number','')])
        for attempt in range(3):
            try:
                localization.translate_texts(texts,'zh')
                return s['id']
            except ValueError:
                if attempt == 2: raise
    with ThreadPoolExecutor(max_workers=3) as pool:
        for section in pool.map(translate_section, sections): print('translated',section,flush=True)
    (root/'frontend-web/src/textbook-zh.json').write_text(json.dumps(localization._cache.get('zh',{}), ensure_ascii=False), encoding='utf-8')
if __name__ == '__main__': main()
