import pytest

from backend.answer_matching import equivalent_blank, numeric_value


@pytest.mark.parametrize('answer', ['6/4', '1.5', '3 * (1/2)', '15e-1', '3/2'])
def test_exact_numeric_equivalence(answer):
    assert equivalent_blank(answer, ['3/2'])


@pytest.mark.parametrize('answer', ['1.49999', '1.50001', '1/0', '2**99999', '1e99999',
                                   '__import__("os")', '(lambda: 1.5)()', '1.5 or 0', 'x+x'])
def test_invalid_or_unequal_input_is_not_accepted(answer):
    assert not equivalent_blank(answer, ['3/2'])


def test_decimal_arithmetic_is_exact_and_symbolic_aliases_preserved():
    assert equivalent_blank('0.1+0.2', ['0.3'])
    assert equivalent_blank(' $ X + X $ ', ['x+x'])
    assert numeric_value('x+x') is None
    assert numeric_value('1+' * 1000 + '1') is None
