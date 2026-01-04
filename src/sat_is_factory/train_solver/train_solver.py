from z3 import Int, IntNumRef, Optimize, RatNumRef, Real, sat

from sat_is_factory.z3_ext import Min

DOCK_DURATION = 0.45133333  # 27.08 sec
CAR_CAPACITY = 32

ABSOLUTE_MAX_TRAINS = 50
ABSOLUTE_MAX_CARS = 50


class Buffer:
    def __init__(self, external_rate, cars, platform_rate):
        self.size = DOCK_DURATION * external_rate / cars
        self.time = self.size / (platform_rate - external_rate / cars)


class Io:
    def __init__(self, kind, ratio_rate, cars, platform_rate):
        self.rate = Real(f"{kind}_rate")
        self.ratio = self.rate / ratio_rate
        self.buffer = Buffer(self.rate, cars, platform_rate)


class Solver:
    def __init__(self, args):
        self.args = args
        self.setup()
        self.optimize()

    def setup(self):
        self.stack_size = Int("stack_size")

        self.trains = Int("trains")
        self.cars = Int("cars")

        self.platform_rate = Int("platform_rate")
        self.station_rate = self.platform_rate * self.cars

        self.rtd = Real("rtd")

        # Train equations
        self.partial = (
            self.platform_rate
            * self.cars
            * (self.rtd - DOCK_DURATION * self.trains)
            / self.rtd
        )
        self.full = CAR_CAPACITY * self.stack_size * self.trains * self.cars / self.rtd
        self.throughput = Min(self.partial, self.full)
        self.efficiency = self.throughput / self.platform_rate / self.cars * 100

        def loaded(fill_rate):
            return

        if self.args.source_rate is None:
            self.fill_rate = self.drain_rate = self.throughput
        else:
            self.source = Io("source", self.throughput, self.cars, self.platform_rate)
            self.fill_rate = Min(self.source.rate, self.throughput)
            self.sink = Io("sink", self.fill_rate, self.cars, self.platform_rate)
            self.drain_rate = Min(self.sink.rate, self.throughput)

        self.loaded = self.fill_rate * self.rtd / (self.trains * self.cars)  # pyright: ignore[reportOperatorIssue]

    def optimize(self):
        self.opt = Optimize()
        self.optimize_train()
        self.optimize_station()
        if self.args.source_rate or self.args.sink_rate:
            self.optimize_source_sink()

    def optimize_train(self):
        if self.args.rtd is not None:
            if self.args.rtd > DOCK_DURATION:
                self.opt.add(self.rtd == self.args.rtd)
            else:
                raise ValueError("invalid rtd")
        else:
            # TODO: IDK why Z3 still returns -inf for RTD when it's not given.
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
        self.opt.add(self.stack_size == self.args.stack_size)
        self.opt.add(self.platform_rate == self.args.platform_rate)
        self.opt.add(self.throughput > 0)  # pyright: ignore[reportOperatorIssue]

        # If neither RTD or throughput are given, we can assume we want a
        # solution for the optimal values of both.
        if (
            self.args.rtd is None
            and self.args.throughput is None
            and self.args.source_rate is None
        ):
            self.info.append("optimal")
            self.opt.add(self.partial == self.full)
        # If a throughput is given, we use that.
        elif self.args.throughput is not None:
            self.info.append(f"minimize throughput >= {self.args.throughput}")
            self.opt.add(self.throughput >= self.args.throughput)
            self.opt.minimize(self.throughput)
        # Otherwise we try to solve for the given source rate.
        elif self.args.source_rate is not None:
            self.info.append(f"minimize throughput >= {self.args.source_rate}")
            self.opt.add(self.throughput >= self.args.source_rate)
            self.opt.minimize(self.throughput)
        # Otherwise we try to solve for the given sink rate.
        elif self.args.sink_rate is not None:
            self.info.append(f"minimize throughput >= {self.args.sink_rate}")
            self.opt.add(self.throughput >= self.args.sink_rate)
            self.opt.minimize(self.throughput)
        # If neither are given, but we have a round trip time, we find the
        # maximum value.
        else:
            self.info.append("maximizing throughput")
            self.opt.maximize(self.throughput)

    def optimize_source_sink(self):
        self.opt.add(self.source.rate == self.args.source_rate)
        if self.args.sink_rate is not None:
            self.opt.add(self.sink.rate == self.args.sink_rate)

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
                "stack_size": z3_to_python(self.stack_size),
                "trains": z3_to_python(self.trains),
                "cars": z3_to_python(self.cars),
                "platform_rate": z3_to_python(self.platform_rate),
                "station_rate": z3_to_python(self.station_rate),
                "loaded": z3_to_python(self.loaded),
                "rtd": z3_to_python(self.rtd),
                "throughput": z3_to_python(self.throughput),
                "efficiency": z3_to_python(self.efficiency),
            }

            if self.args.source_rate is not None:
                solution |= {
                    "source": {
                        "rate": z3_to_python(self.source.rate),
                        "ratio": z3_to_python(self.source.ratio),
                        "buffer": {
                            "size": z3_to_python(self.source.buffer.size),
                            "time": z3_to_python(self.source.buffer.time),
                        },
                    },
                    "fill_rate": z3_to_python(self.fill_rate),
                }
            if self.args.sink_rate is not None:
                solution |= {
                    "sink": {
                        "rate": z3_to_python(self.sink.rate),
                        "ratio": z3_to_python(self.sink.ratio),
                        "buffer": {
                            "size": z3_to_python(self.sink.buffer.size),
                            "time": z3_to_python(self.sink.buffer.time),
                        },
                    },
                    "drain_rate": z3_to_python(self.drain_rate),
                }

            return solution
