from z3 import Int, IntNumRef, Optimize, RatNumRef, Real, sat

from sat_is_factory.z3_ext import Min

DOCK_DURATION = 0.45133333  # 27.08 sec
CAR_CAPACITY = 32

ABSOLUTE_MAX_TRAINS = 50
ABSOLUTE_MAX_CARS = 50


class TrainSolver:
    def __init__(self, args):
        self.args = args
        self.setup()
        self.optimize()

    def setup(self):
        self.stack = Int("stack")
        self.platform_rate = Int("platform_rate")
        self.trains = Int("trains")
        self.cars = Int("cars")
        self.rtd = Real("rtd")

        # Train equation
        self.partial = (
            self.platform_rate
            * self.cars
            * (self.rtd - DOCK_DURATION * self.trains)
            / self.rtd
        )
        self.full = CAR_CAPACITY * self.stack * self.trains * self.cars / self.rtd
        self.throughput = Min(self.partial, self.full)

        if self.args.input_rate is None:
            self.loaded = self.throughput * self.rtd / (self.trains * self.cars)
        else:
            self.setup_io()
            self.loaded = (
                Min(self.throughput, self.input_rate)
                * self.rtd
                / (self.trains * self.cars)
            )

    def setup_io(self):
        self.input_rate = Real("input_rate")
        self.output_rate = Real("output_rate")

        self.output_rate = Min(self.throughput, self.input_rate)

        self.input_buffer_size = DOCK_DURATION * self.input_rate
        self.input_buffer_time = self.input_buffer_size / (
            self.platform_rate - self.input_rate
        )

        self.output_buffer_size = DOCK_DURATION * self.output_rate
        self.output_buffer_time = self.output_buffer_size / (
            self.platform_rate - self.output_rate
        )

    def optimize(self):
        self.opt = Optimize()
        self.optimize_train()
        self.optimize_station()
        if self.args.input_rate:
            self.optimize_io()

    def optimize_train(self):
        if self.args.rtd is not None:
            if self.args.rtd > DOCK_DURATION:
                self.opt.add(self.rtd == self.args.rtd)
            else:
                raise ValueError("invalid rtd")
        else:
            self.opt.add(self.rtd >= DOCK_DURATION)

        self.opt.add(self.trains > 0)
        self.opt.add(self.trains <= ABSOLUTE_MAX_TRAINS)
        if (
            self.args.max_trains
            and self.args.trains
            and self.args.max_trains < self.args.trains
        ):
            raise ValueError("invalid --trains and --max-trains arguments")
        if self.args.max_trains is not None:
            self.opt.add(self.trains <= self.args.max_trains)
        if self.args.trains is not None:
            self.opt.add(self.trains == self.args.trains)

        self.opt.add(self.cars > 0)
        self.opt.add(self.cars <= ABSOLUTE_MAX_CARS)
        if (
            self.args.max_cars
            and self.args.cars
            and self.args.max_cars < self.args.cars
        ):
            raise ValueError("invalid --cars and --max-cars arguments")
        if self.args.max_cars is not None:
            self.opt.add(self.cars <= self.args.max_cars)
        if self.args.cars is not None:
            self.opt.add(self.cars == self.args.cars)

        self.info = []

        minimize = ["cars", "trains"]
        if self.args.minimize is not None:
            try:
                minimize.remove(self.args.minimize)
            except ValueError:
                raise ValueError(
                    "invalid minimization priority, must be one of 'cars' or 'trains'"
                )
            minimize.insert(0, self.args.minimize)

        for var in minimize:
            if getattr(self.args, var) is None:
                self.info.append(f"minimize {var}")
                self.opt.minimize(getattr(self, var))

        if self.args.rtd is None:
            self.info.append("minimize rtd")
            self.opt.minimize(self.rtd)

    def optimize_station(self):
        self.opt.add(self.stack == self.args.stack)
        self.opt.add(self.platform_rate == self.args.platform_rate)
        self.opt.add(self.throughput > 0)

        # If neither RtD or throughput are given, we can assume we want a
        # solution for the optimal values of both.
        if (
            self.args.rtd is None
            and self.args.throughput is None
            and self.args.input_rate is None
        ):
            self.info.append("optimal")
            self.opt.add(self.partial == self.full)
        # If a throughput is given, we use that.
        elif self.args.throughput is not None:
            self.info.append(f"minimize throughput >= {self.args.throughput}")
            self.opt.add(self.throughput >= self.args.throughput)
            self.opt.minimize(self.throughput)
        # Otherwise we try to solve for the given input rate.
        elif self.args.input_rate is not None:
            self.info.append(f"minimize throughput >= {self.args.input_rate}")
            self.opt.add(self.throughput >= self.args.input_rate)
            self.opt.minimize(self.throughput)
        # If neither are given, but we have a round trip time, we find the
        # maximum value.
        else:
            self.info.append("maximizing throughput")
            self.opt.maximize(self.throughput)

    def optimize_io(self):
        self.opt.add(self.input_rate == self.args.input_rate)

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

            if z3_to_python(self.trains) == ABSOLUTE_MAX_TRAINS:
                print("warning: absolute maximum train limit reached in solver")
            if z3_to_python(self.cars) == ABSOLUTE_MAX_CARS:
                print("warning: absolute maximum car limit reached in solver")

            solution = {
                "info": self.info,
                "stack": z3_to_python(self.stack),
                "platform_rate": z3_to_python(self.platform_rate),
                "trains": z3_to_python(self.trains),
                "cars": z3_to_python(self.cars),
                "loaded": z3_to_python(self.loaded),
                "rtd": z3_to_python(self.rtd),
                "throughput": z3_to_python(self.throughput),
            }

            if self.args.input_rate is not None:
                solution |= {
                    "input": {
                        "rate": z3_to_python(self.input_rate),
                        "buffer": {
                            "size": z3_to_python(self.input_buffer_size),
                            "time": z3_to_python(self.input_buffer_time),
                        },
                    },
                    "output": {
                        "rate": z3_to_python(self.output_rate),
                        "buffer": {
                            "size": z3_to_python(self.output_buffer_size),
                            "time": z3_to_python(self.output_buffer_time),
                        },
                    },
                }

            return solution
