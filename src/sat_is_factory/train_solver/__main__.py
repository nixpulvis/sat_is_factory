import argparse
import math

from sat_is_factory.train_solver import TrainSolver
from sat_is_factory.train_solver.train_solver import CAR_CAPACITY
from sat_is_factory.util import fmt_time, pluralize, time

HELP = """
This program can be used to solve the train throughput equations for single or
multiple train/car setups.

Depending on the input flags, the program will either:

- Solve the optimal RTD and throughput, when neither are provided
- Minimize the system while achieving a given --throughput
- Maximize the throughput for a given --rtd

Throughput (--given by --throughput) is the total amount a train system can
handle with all trains and cars in the system. This value may be larger than the
given --source and --sink values if specified.

RTD (given by --rtd) is the Round Trip Duration for any one specific train. This
is most easily measured by timing the duration of a train from "toot-to-toot".
If there is congestion on the tracks, then an average should be used for closest
results.

The platform rate (given by --platform) is the total input/output rate for a
single platform. This is usually 2x the speed of whatever kind of belt/pipe you
have connected to it.

The --source argument allows calculating source platform(s) buffer information.
The --sink option further allows ensuring a final consistent rate to downstream
consumers of the unloading platform(s). If you pass just --sink, it will set
--source to be equal. These calculations assume each platform has the same
platform rate and that the source and sink are properly balanced. Balancing
train stations is sometimes needed to achieve maximum throughput when using the
wait until fully loaded/unloaded option in game.

It is impossible to achieve perfect platform efficiency due to the docking delay
in the game, so don't expect to see (100% platform efficiency), this tool can
help you achieve 100% of source throughput however.

Take note of the default values, which assume common stack sizes of 100 and
maximum platform speeds of 2,400 items/min (or 1,200 m^3/min for fluids). There
are also somewhat reasonable default maximum values for the number of trains and
cars per train.

Use the `--minimize trains` flag if you wish to solve for routes with fewer
trains while increasing the number of cars per train. The default is to minimize
cars, since A) it's much easier to add trains (ignoring congestion) and B) the
math for adding cars is much simpler.

For results with more than one train, it is assumed that they are evenly spaced
and doing so is up to you to implement correctly in-game. If the result calls
for fully loaded trains, one method to achieve this to set the train to wait
until it's fully loaded/unloaded AND 0 seconds. A more generic method, if the
train is partially loaded, or carrying other items, is to set the train to wait
until one load/unload AND `RTD / number of trains` (TODO: test this).

For pipes, use --fluid, which sets the "stack" size appropriately to 50.
"""


class StackSentinal:
    def items(self):
        return 100

    def fluids(self):
        return 1600 / CAR_CAPACITY

    def __str__(self):
        return str(self.items())


class PlatformSentinal:
    def item_rate(self):
        return 2400

    def fluid_rate(self):
        return 1200

    def __str__(self):
        return f"{self.item_rate()} items/min or {self.fluid_rate()} m^3/min"


STACK_SENTINAL = StackSentinal()
PLATFORM_SENTINAL = PlatformSentinal()


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


def get_arguments():
    parser = argparse.ArgumentParser(
        description=HELP,
        formatter_class=Formatter,
    )

    constants = parser.add_argument_group("constants")
    constants.add_argument(
        "--stack", type=int, default=STACK_SENTINAL, help="Item stack quantity"
    )
    constants.add_argument(
        "--platform",
        type=int,
        dest="platform_rate",
        default=PLATFORM_SENTINAL,
        help="Platform loading speed",
    )
    constants.add_argument(
        "--fluid",
        action="store_true",
        help="Using fluids",
    )

    train = parser.add_argument_group("train constraints")
    train.add_argument(
        "--trains", type=int, help="Number of trains, otherwise minimized"
    )
    train.add_argument(
        "--max-trains", type=int, default=10, help="Maximum number of trains"
    )
    train.add_argument("--cars", type=int, help="Number of cars, otherwise minimized")
    train.add_argument(
        "--max-cars", type=int, default=10, help="Maximum number of cars"
    )
    train.add_argument(
        "--minimize",
        type=str,
        default="cars",
        help="Prioritize minimizing either `trains`, `cars`",
    )

    route = parser.add_argument_group("route constraints")
    route.add_argument(
        "--rtd", type=time, help="Round trip duration, otherwise minimized"
    )
    route.add_argument(
        "--throughput", type=float, help="Minimum throughput, otherise maximized"
    )

    io = parser.add_argument_group("source and sink values")
    io.add_argument(
        "--input",
        "--source",
        type=float,
        dest="source_rate",
        help="Source input rate",
    )
    io.add_argument(
        "--sink",
        type=float,
        dest="sink_rate",
        help="Output sink rate",
    )

    args = parser.parse_args()

    set_io_defaults(args)
    set_additional_defaults(parser, args)

    if args.source_rate is not None:
        if args.source_rate == 0:
            parser.error("--source cannot be 0")
        elif args.source_rate < 0:
            parser.error("--source cannot be negative")
    if args.sink_rate is not None:
        if args.sink_rate == 0:
            parser.error("--sink cannot be 0")
        elif args.sink_rate < 0:
            parser.error("--sink cannot be negative")

    return args


def set_io_defaults(args):
    if args.sink_rate is not None and args.source_rate is None:
        args.source_rate = args.sink_rate


def set_additional_defaults(parser, args):
    if args.fluid:
        if args.stack == STACK_SENTINAL:
            args.stack = STACK_SENTINAL.fluids()
        else:
            parser.error("cannot use --stack with --fluid")
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = PLATFORM_SENTINAL.fluid_rate()
    else:
        if args.stack == STACK_SENTINAL:
            args.stack = STACK_SENTINAL.items()
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = PLATFORM_SENTINAL.item_rate()


def main():
    args = get_arguments()

    try:
        solver = TrainSolver(args)
        print(", ".join(solver.info))
        print()

        solution = solver.solve()
        if solution is not None:
            if args.fluid:
                unit = "m^3"
            else:
                unit = "items"
            print_solution(solution, unit)
        else:
            print("No solution found.")

    except ValueError as e:
        print(f"Error: {e}")


def print_solution(solution, unit):
    print_train_solution(solution, unit)
    print_station_solution(solution, unit)
    if "source" in solution or "sink" in solution:
        print()
        print_io_solution(solution, unit)


def print_train_solution(solution, unit):
    if solution["loaded"] < CAR_CAPACITY * solution["stack"]:
        loaded_kind = "partially filled"
    else:
        loaded_kind = "full"
    print(pluralize("train", solution["trains"]))
    print(pluralize("car", solution["cars"]))
    stacks = math.ceil(solution["loaded"] / solution["stack"])
    print(
        f"{loaded_kind} with {round(solution['loaded'])} {unit}",
        end="",
    )
    if unit == "items":
        print(f" in {pluralize('stack', stacks)}", end="")
    if (
        "source" in solution
        and "sink" in solution
        and solution["fill_rate"] > solution["drain_rate"]
    ):
        print(" (eventually filled)", end="")
    print()
    print(f"{fmt_time(solution['rtd'])} per round trip.")


def print_station_solution(solution, unit):
    total_rate = solution["platform_rate"] * solution["cars"]
    plural_platform = pluralize("platform", solution["cars"], name_only=True)
    print(f"{total_rate} {unit}/min total active rate of {plural_platform}")
    efficiency = (
        solution["throughput"] / solution["platform_rate"] / solution["cars"] * 100
    )
    print(
        f"{round(solution['throughput'], 2)} {unit}/min throughput ({round(efficiency, 2)}% platform efficiency)"
    )


def print_io_solution(solution, unit):
    plural_buffer = pluralize("buffer", solution["cars"], name_only=True)

    if "source" in solution:
        source_ratio = solution["source"]["rate"] / solution["throughput"] * 100
        source_ratio_msg = f"{round(source_ratio, 2)}% of throughput"
        print(
            f"{round(solution['source']['rate'], 2)} {unit}/min source rate ({source_ratio_msg})"
        )
        if "drain_rate" in solution:
            full = solution["source"]["rate"] > solution["drain_rate"]
        else:
            full = solution["source"]["rate"] > solution["throughput"]
        if not full:
            source_buffer_size = math.ceil(solution["source"]["buffer"]["size"])
            source_buffer_time = fmt_time(solution["source"]["buffer"]["time"])
            print(
                f"{source_buffer_size} {unit} in source {plural_buffer} empties after {source_buffer_time}"
            )
        else:
            print("source buffer would be full")

    print(f"{round(solution['fill_rate'], 2)} {unit}/min available")

    if "sink" in solution:
        sink_ratio = solution["sink"]["rate"] / solution["fill_rate"] * 100
        sink_ratio_msg = f"{round(sink_ratio, 2)}% of available"
        print(
            f"{round(solution['sink']['rate'], 2)} {unit}/min sink rate ({sink_ratio_msg})"
        )
        empty = solution["sink"]["rate"] > solution["fill_rate"]
        if not empty:
            sink_buffer_size = math.ceil(solution["sink"]["buffer"]["size"])
            sink_buffer_time = fmt_time(solution["sink"]["buffer"]["time"])
            print(
                f"{sink_buffer_size} {unit} in sink {plural_buffer} fills after {sink_buffer_time}"
            )
        else:
            print("sink buffer would be empty")


if __name__ == "__main__":
    main()
