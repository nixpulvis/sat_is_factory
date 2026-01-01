from z3 import Int, IntNumRef, Optimize, RatNumRef, Real, sat

from sat_is_factory.z3_ext import Min

DOCK_DURATION = 0.45133333  # 27.08 sec
CAR_CAPACITY = 32

ABSOLUTE_MAX_TRAINS = 50
ABSOLUTE_MAX_CARS = 50


class TrainSolver:
    def __init__(self, args):
        self.rtd = Real("rtd")
        self.platform_rate = Int("platform_rate")
        self.stack = Int("stack")

        self.trains = Int("trains")
        self.cars = Int("cars")

        # Train equation
        self.partial = (
            self.platform_rate
            * self.cars
            * (self.rtd - DOCK_DURATION * self.trains)
            / self.rtd
        )
        self.full = CAR_CAPACITY * self.stack * self.trains * self.cars / self.rtd
        self.throughput = Min(self.partial, self.full)

        self.opt = Optimize()
        self.opt.add(self.throughput > 0)

        self.opt.add(self.stack == args.stack)
        self.opt.add(self.platform_rate == args.platform_rate)

        if args.rtd is not None:
            if args.rtd > DOCK_DURATION:
                self.opt.add(self.rtd == args.rtd)
            else:
                raise ValueError("invalid rtd")
        else:
            self.opt.add(self.rtd >= DOCK_DURATION)

        self.opt.add(self.trains > 0)
        self.opt.add(self.trains <= ABSOLUTE_MAX_TRAINS)
        if args.max_trains and args.trains and args.max_trains < args.trains:
            raise ValueError("invalid --trains and --max-trains arguments")
        if args.max_trains is not None:
            self.opt.add(self.trains <= args.max_trains)
        if args.trains is not None:
            self.opt.add(self.trains == args.trains)

        self.opt.add(self.cars > 0)
        self.opt.add(self.cars <= ABSOLUTE_MAX_CARS)
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

        # If neither RtD or throughput are given, we can assume we want a
        # solution for the optimal values of both.
        if args.rtd is None and args.throughput is None:
            self.info.append("solving optimal")
            self.opt.add(self.partial == self.full)
        # If a throughput is given, then we
        elif args.throughput is not None:
            self.info.append(f"minimize throughput >= {args.throughput}")
            self.opt.add(self.throughput >= args.throughput)
            self.opt.minimize(self.throughput)
        else:
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

            if z3_to_python(self.trains) == ABSOLUTE_MAX_TRAINS:
                print("warning: absolute maximum train limit reached in solver")
            if z3_to_python(self.cars) == ABSOLUTE_MAX_CARS:
                print("warning: absolute maximum car limit reached in solver")

            return {
                "info": self.info,
                "stack": z3_to_python(self.stack),
                "platform_rate": z3_to_python(self.platform_rate),
                "trains": z3_to_python(self.trains),
                "cars": z3_to_python(self.cars),
                "rtd": z3_to_python(self.rtd),
                "throughput": z3_to_python(self.throughput),
                "loaded": is_loaded(),
            }
