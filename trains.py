import argparse
from z3 import *

DOCK_DURATION = 0.45133333
CAR_CAPACITY = 32

def calculate_throughput(args):
    partial = 2 * args.belt * args.cars * (args.rtd - DOCK_DURATION * args.trains) / args.rtd
    full = CAR_CAPACITY * args.stack * args.trains * args.cars / args.rtd
    throughput = min(partial, full)
    print(f"stack size: {args.stack}")
    print(f"belt speed: {args.belt}")
    print()
    print(f"round trip duration: {args.rtd}")
    print(f"trains: {args.trains}")
    print(f"cars: {args.cars}")
    if partial > full:
        loaded = "full"
    else:
        loaded = "partial"
    print(f"throughput ({loaded}): {throughput}")



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

    if args.trains is not None:
        opt.add(trains <= args.trains)
    else:
        opt.add(trains > 0)

    if args.cars is not None:
        opt.add(cars <= args.cars)
    else:
        opt.add(cars > 0)

    if args.throughput is not None:
        opt.add(throughput >= args.throughput)
        opt.maximize(throughput)
    else:
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
        if z3_to_python(model.eval(partial)) > z3_to_python(model.eval(full)):
            loaded = "full"
        else:
            loaded = "partial"
        print_param("throughput ({loaded})", throughput)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TODO",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    solve_parser = subparsers.add_parser('solve', help='TODO')
    solve_parser.add_argument("--stack", type=int, default=100, help="Item stack quantity")
    solve_parser.add_argument("--belt", type=int, default=1200, help="Max belt speed")
    solve_parser.add_argument("--rtd", type=float, help="Round trip time, otherwise optimized for")
    solve_parser.add_argument("--trains", type=int, help="Max number of trains")
    solve_parser.add_argument("--cars", type=int, help="Max number of cars")
    solve_parser.add_argument("--throughput", type=float, help="Min throughput needed")

    calculate_parser = subparsers.add_parser('calculate', help='TODO')
    calculate_parser.add_argument("--stack", type=int, default=100, help="Item stack quantity")
    calculate_parser.add_argument("--belt", type=int, default=1200, help="Belt speed")
    calculate_parser.add_argument("--rtd", type=float, required=True, help="Round trip time")
    calculate_parser.add_argument("--trains", type=int, default=1, help="Number of trains")
    calculate_parser.add_argument("--cars", default=1, type=int, help="Number of cars")



    args = parser.parse_args()

    if args.command == "calculate":
        calculate_throughput(args)
    elif args.command == "solve":
        solve_throughput(args)

