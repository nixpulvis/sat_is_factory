import argparse
from z3 import *

DOCK_DURATION = 0.45133333
CAR_CAPACITY = 32

def solve_throughput(args):
    def z3_min(a, b):
        return If(a < b, a, b)

    def z3_to_python(v):
        if isinstance(v, IntNumRef):
            return v.as_long()
        elif isinstance(v, RatNumRef):
            return v.numerator_as_long() / v.denominator_as_long()

    rtd = Real('rtd')
    belt = Int('belt')
    stack = Int('stack')

    trains = Int('trains')
    cars = Int('cars')

    # Train equation
    partial = 2 * belt * cars * (rtd - DOCK_DURATION * trains) / rtd
    full = CAR_CAPACITY * stack * trains * cars / rtd
    throughput = z3_min(partial, full)

    opt = Optimize()

    opt.add(stack == args.stack)
    opt.add(belt == args.belt)

    if args.rtd is not None:
        if args.rtd > DOCK_DURATION:
            opt.add(rtd == args.rtd)
        else:
            raise "invalid rtd"
    else:
        opt.add(rtd >= DOCK_DURATION)

    opt.add(trains > 0)
    if args.trains is not None:
        opt.add(trains <= args.trains)

    opt.add(cars > 0)
    if args.cars is not None:
        opt.add(cars <= args.cars)


    if args.rtd is None or args.throughput is None:
        opt.add(partial == full)
    else:
        opt.maximize(throughput)

    if args.throughput is not None:
        opt.add(throughput >= args.throughput)

    opt.minimize(trains)
    opt.minimize(cars)

    if opt.check() == sat:
        model = opt.model()

        def print_param(label, param):
            print(f"{label} = {z3_to_python(model.eval(param))}")

        print("Fixed:")
        print_param("stack size", stack)
        print_param("belt speed", belt)
        print()
        print("Solved:")
        print_param("round trip duration", rtd)
        print_param("trains", trains)
        print_param("cars", cars)
        if z3_to_python(model.eval(partial)) >= z3_to_python(model.eval(full)):
            loaded = "full"
        else:
            loaded = "partial"
        print_param(f"throughput ({loaded})", throughput)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TODO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--stack", type=int, default=100, help="Item stack quantity")
    parser.add_argument("--belt", type=int, default=1200, help="Max belt speed")
    parser.add_argument("--rtd", type=float, help="Round trip time, otherwise optimized for")
    parser.add_argument("--trains", type=int, help="Max number of trains")
    parser.add_argument("--cars", type=int, help="Max number of cars")
    parser.add_argument("--throughput", type=float, help="Min throughput needed")

    args = parser.parse_args()
    solve_throughput(args)

