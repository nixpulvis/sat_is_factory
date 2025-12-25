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

        minimize = ["cars", "trains"]
        if args.minimize is not None:
            try:
                minimize.remove(args.minimize)
            except ValueError:
                raise ValueError(
                    "invalid minimization priority, must be one of 'cars' or 'trains'"
                )
            minimize.insert(0, args.minimize)

        for var in minimize:
            if getattr(args, var) is None:
                self.info.append(f"minimize {var}")
                self.opt.minimize(getattr(self, var))

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
                "stack": z3_to_python(self.stack),
                "belt": z3_to_python(self.belt),
                "trains": z3_to_python(self.trains),
                "cars": z3_to_python(self.cars),
                "rtd": z3_to_python(self.rtd),
                "throughput": z3_to_python(self.throughput),
                "loaded": is_loaded(),
            }
