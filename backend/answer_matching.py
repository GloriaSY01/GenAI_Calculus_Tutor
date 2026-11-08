"""Conservative exact numeric equivalence, without evaluating student code."""
import ast
import re
from fractions import Fraction


def numeric_value(value: str) -> Fraction | None:
    source = value.strip().replace('$', '').replace('−', '-').replace('^', '**')
    if len(source) > 128 or not re.fullmatch(r'[0-9eE.+*/()\s-]+', source):
        return None
    if any(abs(int(exponent)) > 100 for exponent in re.findall(r'[eE]([+-]?\d+)', source)):
        return None
    try:
        tree = ast.parse(source, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 40:
            return None

        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                result = Fraction(ast.get_source_segment(source, node))
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                result = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
            elif isinstance(node, ast.BinOp):
                left, right = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Add):
                    result = left + right
                elif isinstance(node.op, ast.Sub):
                    result = left - right
                elif isinstance(node.op, ast.Mult):
                    result = left * right
                elif isinstance(node.op, ast.Div):
                    result = left / right
                elif isinstance(node.op, ast.Pow) and right.denominator == 1 and abs(right) <= 12:
                    result = left ** int(right)
                else:
                    raise ValueError('Unsupported operation')
            else:
                raise ValueError('Not a numeric expression')
            if max(result.numerator.bit_length(), result.denominator.bit_length()) > 4096:
                raise ValueError('Numeric expression too large')
            return result

        return visit(tree.body)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError, TypeError):
        return None


def equivalent_blank(answer: str, accepted: list[str]) -> bool:
    normalize = lambda text: text.strip().lower().replace(' ', '').replace('$', '')
    if normalize(answer) in {normalize(value) for value in accepted}:
        return True
    numeric = numeric_value(answer)
    return numeric is not None and any(numeric_value(value) == numeric for value in accepted)
