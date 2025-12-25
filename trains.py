import argparse

from z3 import If, Int, IntNumRef, Optimize, RatNumRef, Real, sat

DOCK_DURATION = 0.45133333
CAR_CAPACITY = 32

# Some basic upper limits on train sizes to help solver when user doesn't
# constrain.
TRAIN_MAX = 50
CAR_MAX = 50


def z3_min(a, b):
    return If(a < b, a, b)


class TrainSolver:
    def __init__(self, args):
        self.rtd = Real("rtd")
        self.belt = Int("belt")
        self.stack = Int("stack")

        self.trains = Int("trains")
        self.cars = Int("cars")

        # Train equation
        self.partial = (
            2
            * self.belt
            * self.cars
            * (self.rtd - DOCK_DURATION * self.trains)
            / self.rtd
        )
        self.full = CAR_CAPACITY * self.stack * self.trains * self.cars / self.rtd
        self.throughput = z3_min(self.partial, self.full)

        self.opt = Optimize()

        self.opt.add(self.stack == args.stack)
        self.opt.add(self.belt == args.belt)

        if args.rtd is not None:
            if args.rtd > DOCK_DURATION:
                self.opt.add(self.rtd == args.rtd)
            else:
                raise ValueError("invalid rtd")
        else:
            self.opt.add(self.rtd >= DOCK_DURATION)

        self.opt.add(self.trains > 0)
        self.opt.add(self.trains <= TRAIN_MAX)
        if args.max_trains and args.trains and args.max_trains < args.trains:
            raise ValueError("invalid --trains and --max-trains arguments")
        if args.max_trains is not None:
            self.opt.add(self.trains <= args.max_trains)
        if args.trains is not None:
            self.opt.add(self.trains == args.trains)

        self.opt.add(self.cars > 0)
        self.opt.add(self.cars <= CAR_MAX)
        if args.max_cars and args.cars and args.max_cars < args.cars:
            raise ValueError("invalid --cars and --max-cars arguments")
        if args.max_cars is not None:
            self.opt.add(self.cars <= args.max_cars)
        if args.cars is not None:
            self.opt.add(self.cars == args.cars)

        self.info = []

        if args.cars is None:
            self.info.append("minimize cars")
            self.opt.minimize(self.cars)
        if args.trains is None:
            self.info.append("minimize trains")
            self.opt.minimize(self.trains)
        if args.rtd is None:
            self.info.append("minimize rtd")
            self.opt.minimize(self.rtd)

        if args.rtd is None and args.throughput is None:
            self.info.append("solving optimal throughput")
            self.opt.add(self.partial == self.full)
        elif args.throughput is not None:
            self.info.append(f"minimize throughput >= {args.throughput}")
            self.opt.add(self.throughput >= args.throughput)
            self.opt.minimize(self.throughput)
        elif args.rtd is not None:
            self.info.append("maximizing throughput")
            self.opt.maximize(self.throughput)

    # TODO: Trains, Cars priority option.
    def solve(self):
        if self.opt.check() == sat:
            model = self.opt.model()

            def z3_to_python(expr):
                evaluated = model.eval(expr)
                if isinstance(evaluated, IntNumRef):
                    return evaluated.as_long()
                elif isinstance(evaluated, RatNumRef):
                    return (
                        evaluated.numerator_as_long() / evaluated.denominator_as_long()
                    )

            def is_loaded():
                partial_val = z3_to_python(self.partial)
                full_val = z3_to_python(self.full)
                if partial_val is not None and full_val is not None:
                    if partial_val >= full_val:
                        return "full"
                    else:
                        return "partial"

            if z3_to_python(self.trains) == TRAIN_MAX:
                print("warning: maximum train limit reached in solver")
            if z3_to_python(self.cars) == CAR_MAX:
                print("warning: maximum car limit reached in solver")

            return {
                "info": self.info,
                "results": {
                    "stack": z3_to_python(self.stack),
                    "belt": z3_to_python(self.belt),
                    "trains": z3_to_python(self.trains),
                    "cars": z3_to_python(self.cars),
                    "rtd": z3_to_python(self.rtd),
                    "throughput": z3_to_python(self.throughput),
                    "loaded": is_loaded(),
                },
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="For pipes, use --stack 50 and --belt=<flowrate>",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--stack", type=int, default=100, help="Item stack quantity")
    parser.add_argument("--belt", type=int, default=1200, help="Belt speed")
    parser.add_argument(
        "--rtd", type=float, help="Round trip time, otherwise optimized for"
    )
    parser.add_argument("--max-trains", type=int, help="Max number of trains")
    parser.add_argument("--trains", type=int, help="Number of trains")
    parser.add_argument("--max-cars", type=int, help="Max number of cars")
    parser.add_argument("--cars", type=int, help="Number of cars")
    parser.add_argument("--throughput", type=float, help="Min throughput needed")

    args = parser.parse_args()
    train_solver = TrainSolver(args)
    solution = train_solver.solve()

    if solution is not None:
        print(", ".join(solution["info"]))
        print(f"Stack Size: {solution['results']['stack']}")
        print(f"Belt Speed: {solution['results']['belt']}")
        print(f"Trains: {solution['results']['trains']}")
        print(f"Cars: {solution['results']['cars']}")
        print(f"Loaded: {solution['results']['loaded']}")
        print(
            f"Round Trip Time: {round(solution['results']['rtd'], 4)} min ({round(solution['results']['rtd'] * 60, 2)} sec)"
        )
        print(f"Throughput: {round(solution['results']['throughput'], 4)} items/min")
