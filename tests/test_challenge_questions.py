"""Chapter coverage and exact-answer checks, with model access prohibited."""
import pytest
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, convert_xor

from backend import challenge_questions as cq, generator, textbook
from backend.math_quality import derivative_correct_indices, validate_question_data
from backend.schemas import GradeRequest


SECTIONS = [textbook.get_section(s['id']) for _, s in textbook.iter_sections()]
FORMATS = ['single_choice', 'multiple_choice', 'fill_blank', 'drag_order']


@pytest.fixture(autouse=True)
def offline_generation(monkeypatch):
    monkeypatch.setattr(generator, '_REGISTRY', {})
    monkeypatch.setattr(generator, '_register', lambda q: generator._REGISTRY.update({q['id']: q}))
    monkeypatch.setattr(generator.llm, 'chat_to_json', lambda *a, **k: pytest.fail('challenge called model'))
    monkeypatch.setattr(generator.rag, 'retrieve', lambda *a, **k: pytest.fail('challenge called RAG'))
    monkeypatch.setattr(generator.textbook, 'exercises_for', lambda *a, **k: [])


@pytest.mark.parametrize('section', SECTIONS, ids=lambda s:s['label'])
@pytest.mark.parametrize('qtype', FORMATS)
@pytest.mark.parametrize('language', ['zh', 'en'])
def test_every_section_format_language_is_available_and_gradable(section, qtype, language):
    question = generator.generate_question(qtype, section['id'], 'medium', language=language,
                                           purpose='challenge', exclude_stems=['previous question'])
    private = generator.get(question.id)
    validate_question_data(private, qtype)
    assert private['generation_method'] == cq.VERSION
    assert question.section_id == section['id'] and question.difficulty == 'medium'
    assert 'correct_indices' not in question.model_dump()
    answer = {
        'single_choice': {'single': private.get('correct_indices', [0])[0]},
        'multiple_choice': {'multiple': private.get('correct_indices')},
        'fill_blank': {'blanks': [values[0] for values in private.get('blank_answers', [])]},
        'drag_order': {'order': private.get('steps_correct')},
    }[qtype]
    assert generator.grade(GradeRequest(question_id=question.id, **answer)).correct
    another = generator.generate_question(qtype, section['id'], 'medium', language=language,
                                          purpose='challenge', exclude_stems=[question.stem])
    assert another.stem != question.stem


@pytest.mark.parametrize('section', SECTIONS, ids=lambda s:s['label'])
def test_displayed_calculation_matches_exact_key(section):
    for a,b in [(2,3),(7,7),(18,4)]:
        _,_,_,answer = cq.exercise(section['label'],a,b,'en')
        calculation = parse_expr(cq.working(section['label'],a,b),
                                 transformations=standard_transformations+(convert_xor,))
        assert sp.simplify(calculation-answer) == 0


@pytest.mark.parametrize('qtype', FORMATS)
def test_fifty_excluded_stems_cannot_exhaust_challenge(qtype, monkeypatch):
    monkeypatch.setattr(cq.random, 'randrange', lambda *args: 2)
    section = SECTIONS[0]
    excluded = []
    for _ in range(51):
        data = cq.question(section, qtype, 'zh', excluded)
        assert data['stem'] not in excluded
        excluded.append(data['stem'])


def test_numeric_derivative_validation_still_rejects_incorrect_key():
    stem = '求 $f(x)=3x^2+1$ 在 $x=2$ 处的导数。'
    assert derivative_correct_indices(stem,['12','6','3','0']) == {0}
    with pytest.raises(ValueError,match='Declared derivative'):
        validate_question_data({'stem':stem,'options':['12','6','3','0'],
                                'correct_index':1,'explanation':'wrong','key_idea':'derivative'},'single_choice')


def test_representative_keys_against_independent_calculus():
    x,t = sp.symbols('x t', real=True)
    a,b = 5,3
    expected = {
        '1.1': ((a*t**2+b*t).subs(t,3)-(a*t**2+b*t).subs(t,1))/2,
        '1.3': sp.diff(a*t**3+b*t,t).subs(t,2),
        '2.2': sp.diff(a*x**3+b*x**2,x).subs(x,2),
        '2.5': sp.diff((a*x+b)/(x+1),x).subs(x,1),
        '2.6': sp.limit((x**2-a*a)/(x-a),x,a),
        '3.3': sp.diff(a*t**3+b*t**2,t,2).subs(t,2),
        '4.1': sp.diff((a*x+1)**3,x).subs(x,0),
        '4.4': sp.diff(sp.atan(a*x),x).subs(x,0),
        '5.4': sp.integrate(2*a*x*(a*x*x+b)**2,(x,0,1)),
        '5.5': sp.integrate(a*x+b,(x,1,3)),
        '5.6': sp.integrate(a*x*x+b,(x,0,3))/3,
        '5.7': sp.diff(sp.integrate(a*t+b,(t,0,x*x)),x).subs(x,1),
        '6.2': sp.diff(a*sp.exp(b*x),x).subs(x,0),
        '6.4': sp.diff(sp.log(a*x*x),x).subs(x,b),
        '7.1': sp.integrate(a*x*sp.exp(x),(x,0,1)),
        '7.2': sp.integrate(a*sp.sin(x)*sp.cos(x),(x,0,sp.pi/2)),
        '7.3': sp.integrate(1/sp.sqrt(a*a-x*x),(x,0,sp.Rational(a,2)))/sp.pi,
        '7.5': sp.integrate(a/x**2,(x,1,sp.oo)),
        '8.1': sp.integrate((a*x)**2,(x,0,1)),
        '8.2': sp.integrate(sp.sqrt(1+sp.Rational(a,3)**2),(x,0,3))**2,
        '8.5': sp.integrate(x*b*x,(x,0,a))/sp.integrate(b*x,(x,0,a)),
        '8.6': sp.integrate(a*x,(x,0,b)),
    }
    for label, answer in expected.items():
        assert sp.simplify(cq.exercise(label,a,b,'en')[3]-answer) == 0, label
