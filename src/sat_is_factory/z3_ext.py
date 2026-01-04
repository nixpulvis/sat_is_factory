from z3 import If, IntNumRef, RatNumRef


def Min(a, b):
    return If(a < b, a, b)


def z3_to_python(model, expr):
    evaluated = model.eval(expr)
    if isinstance(evaluated, IntNumRef):
        return evaluated.as_long()
    elif isinstance(evaluated, RatNumRef):
        return evaluated.numerator_as_long() / evaluated.denominator_as_long()
