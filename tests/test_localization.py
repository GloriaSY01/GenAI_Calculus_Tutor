import pytest
from backend import localization

@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(localization, '_cache', {})
    monkeypatch.setattr(localization, 'CACHE_FILE', tmp_path / 'translations.json')

def test_preserves_latex_and_reuses_cache(monkeypatch):
    calls=[]
    def reply(*args, **kwargs):
        calls.append(1)
        return {'translations':['计算 __MATH_0__。']}
    monkeypatch.setattr(localization.llm, 'chat_json', reply)
    source=r'Evaluate $\frac{x^2}{2}$.'
    expected=r'计算 $\frac{x^2}{2}$。'
    assert localization.translate_texts([source], 'zh')[source] == expected
    assert localization.translate_texts([source], 'zh')[source] == expected
    assert len(calls)==1

def test_rejects_missing_math_in_translation(monkeypatch):
    monkeypatch.setattr(localization.llm, 'chat_json', lambda *a, **k: {'translations':['计算。']})
    with pytest.raises(ValueError): localization.translate_texts(['Evaluate $x^2$.'], 'zh')
    assert not localization.CACHE_FILE.exists()

def test_formula_and_english_original_need_no_model(monkeypatch):
    def fail(*args, **kwargs): raise AssertionError('Unnecessary model call')
    monkeypatch.setattr(localization.llm, 'chat_json', fail)
    assert localization.translate_texts(['$x+1$'], 'zh') == {'$x+1$':'$x+1$'}
    assert localization.translate_texts(['Velocity and Distance'], 'en') == {'Velocity and Distance':'Velocity and Distance'}


def test_preserves_bare_function_notation(monkeypatch):
    def reply(*args, **kwargs):
        raise AssertionError('Pure function notation must not be sent for translation')

    monkeypatch.setattr(localization.llm, 'chat_json', reply)
    translated = localization.translate_texts(['cos(x)', '-sin(x)'], 'zh')

    assert translated == {'cos(x)': 'cos(x)', '-sin(x)': '-sin(x)'}


def test_repairs_cached_chinese_function_notation(monkeypatch):
    monkeypatch.setattr(localization, '_cache', {'zh': {'cos(x)': '余弦(x)'}})
    assert localization.translate_texts(['cos(x)'], 'zh') == {'cos(x)': 'cos(x)'}
