import json
from collections import Counter
from pathlib import Path
from backend import rag, textbook

ROOT = Path(__file__).resolve().parents[1] / 'data/textbook/mit-calculus'

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))

def test_learn_page_uses_curated_formulas_after_chapter_one():
    card = rag.section_page('mit-2-1-the-derivative-of-a-function')
    formulas = [formula for block in card['content'] for formula in block['formulas']]
    assert any(formula.startswith('\\displaystyle') for formula in formulas)
    assert 'mit-2-1-concept-001' not in {block['id'] for block in card['content']}

def test_all_formulas_have_overrides():
    overrides = rag._formula_overrides()
    for row in read('verified_content.json'):
        assert len(overrides[row['id']]) == len(row['formulas'])

def test_extracted_images_have_explanations_or_existing_crops():
    covered = set(read('illustration_notes.json'))
    covered |= {f'pdf-figure-1-{page}-1' for page in [2, 4, 10, 11, 13, 20]}
    assert set(read('extracted_figures.json')) <= covered

def test_illustration_blocks_stay_in_their_own_section(monkeypatch):
    monkeypatch.setattr(rag, 'get_by_metadata', lambda **kw: [{
        'id': 'fixture', 'content_type': 'concept', 'title': 'Fixture',
        'text': 'Fixture text.', 'pdf_page': 1, 'order': 1, 'figure_ids': [],
        'source': 'MIT Calculus', 'section_id': kw['section_id'],
    }])
    found = Counter()
    extracted = read('extracted_figures.json')
    notes = read('illustration_notes.json')
    for _, section in textbook.iter_sections():
        meta = textbook.get_section(section['id'])
        card = rag.section_page(section['id'])
        for block in card['content']:
            if block['subtype'] != 'illustrated_concept':
                continue
            figure = block['figures'][0]
            original = extracted[figure['id']]
            assert int(meta['chapter_id'].removeprefix('mit-ch')) == original['chapter']
            assert meta['pdf_page_start'] <= original['pdf_page'] <= meta['pdf_page_end']
            assert block['text'] and figure['caption']
            found[figure['id']] += 1
    assert set(found) == set(notes) & set(extracted)
    assert set(found.values()) == {1}
