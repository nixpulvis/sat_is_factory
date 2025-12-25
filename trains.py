import argparse
from z3 import *

def z3_min(a, b):
    return If(a < b, a, b)

def z3_to_python(v):
    if isinstance(v, IntNumRef):
        return v.as_long()
    elif isinstance(v, RatNumRef):
        return v.numerator_as_long() / v.denominator_as_long()

DOCK_DURATION = 0.45133333
CAR_CAPACITY = 32

def throughput(fixed_rtd, fixed_stack, max_belt, max_trains, max_cars, min_tp):
    rtd = Real('rtd')
    belt = Int('belt')
    stack = Int('stack')

    trains = Int('trains')
    cars = Int('cars')

    # Train equation
    partial = 2 * belt * cars * (rtd - DOCK_DURATION * trains) / rtd
    full = CAR_CAPACITY * stack * trains * cars / rtd
    tp = z3_min(partial, full)

    opt = Optimize()

    opt.add(trains > 0)
    opt.add(cars > 0)

    if fixed_rtd:
        opt.add(rtd == fixed_rtd)
    else:
        opt.add(rtd > 0)
    if fixed_stack:
        opt.add(stack == fixed_stack)
    if max_belt:
        opt.add(belt == max_belt)
    else:
        opt.add(belt == 1200)
    if max_trains:
        opt.add(trains <= max_trains)
    if max_cars:
        opt.add(cars <= max_cars)
    if min_tp:
        opt.add(tp >= min_tp)

    opt.minimize(trains)
    opt.minimize(cars)

    if opt.check() == sat:
        model = opt.model()

        def print_param(label, param):
            print(f"{label} = {z3_to_python(model.eval(param))}")

        print_param("round trip duration", rtd)
        print_param("belt speed", belt)
        print_param("stack size", stack)
        print_param("trains", trains)
        print_param("cars", cars)
        print_param("throughput", tp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TODO")
    parser.add_argument("--rtd", type=float, help="Round trip time")
    parser.add_argument("--stack", type=int, help="Item stack quantity")
    parser.add_argument("--belt", type=int, help="Max belt speed")
    parser.add_argument("--trains", type=int, help="Max number of trains")
    parser.add_argument("--cars", type=int, help="Max number of cars")
    parser.add_argument("--throughput", type=float, help="Min throughput needed")

    args = parser.parse_args()

    throughput(args.rtd, args.stack, args.belt, args.trains, args.cars, args.throughput)

