from z3 import If


def Min(a, b):
    return If(a < b, a, b)
