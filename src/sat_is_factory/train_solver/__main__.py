import argparse
import math
import re

from sat_is_factory.train_solver import TrainSolver
from sat_is_factory.train_solver.train_solver import CAR_CAPACITY

STACK_SENTINAL = object()
PLATFORM_SENTINAL = object()


class Formatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


def time(str):
    match = re.search("(?P<minutes>\\d+):(?P<seconds>\\d+(\\.\\d+)?)", str)
    if match:
        minutes = int(match.group("minutes"))
        seconds = float(match.group("seconds"))
        return minutes + seconds / 60.0
    else:
        return float(str)


def fmt_time(minutes):
    m, s = divmod(minutes * 60, 60)
    m, s = int(m), round(s, 2)
    if m > 0:
        return f"{m} min {s} sec"
    else:
        return f"{s} sec"


# Super incomplete for all of English, but enough for now.
def pluralize(name, count):
    if count == 1:
        return f"{count} {name}"
    else:
        return f"{count} {name}s"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
This program can be used to solve the train throughput equations for single or
multi train/car setups.

Depending on the input flags, the program will either:

- Solve the optimal RTD and throughput, when neither are provided
- Minimize the system while achieving a given throughput
- Maximize the throughput for a given RTD

RTD is the Round Trip Duration for any one specific train. This is most easily
measured by timing the duration of a train from "toot-to-toot". If there is
congestion on the tracks, then an average should be used for closest results.

It is impossible to achieve perfect platform efficiency due to the docking delay
in the game, so don't expect to see (100% platform efficiency), this tool can
help you achieve 100% of input throughput however.

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
""",
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
        help="Platform loading speed (sum of belt/pipe speeds)",
    )
    constants.add_argument(
        "--fluid",
        action="store_true",
        help="Using fluids (sets --stack to 50)",
    )
    constants.add_argument(
        "--input",
        type=float,
        dest="input_rate",
        help="Input rate (TODO: split between platforms)",
    )

    train = parser.add_argument_group("train constraints")
    train.add_argument(
        "--trains", type=int, help="Number of trains, otherwise optimized for"
    )
    train.add_argument(
        "--max-trains", type=int, default=10, help="Maximum number of trains"
    )
    train.add_argument(
        "--cars", type=int, help="Number of cars, otherwise optimized for"
    )
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
        "--rtd", type=time, help="Round trip duration, otherwise optimized for"
    )
    route.add_argument("--throughput", type=float, help="Minimum throughput")

    args = parser.parse_args()

    if args.fluid:
        if args.stack == STACK_SENTINAL:
            args.stack = 1600 / CAR_CAPACITY
        else:
            raise ValueError("cannot use --stack with --fluid")
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = 1200
    else:
        if args.stack == STACK_SENTINAL:
            args.stack = 100
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = 2400

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

            if solution["loaded"] < CAR_CAPACITY * solution["stack"]:
                loaded_kind = "partially filled"
            else:
                loaded_kind = "full"
            print(pluralize("train", solution["trains"]))
            print(pluralize("car", solution["cars"]))
            stacks = math.ceil(solution["loaded"] / solution["stack"])
            print(
                f"{loaded_kind} with {round(solution['loaded'])} {unit} ({pluralize('stack', stacks)})"
            )
            print(f"{fmt_time(solution['rtd'])} per round trip.")

            if args.input_rate:
                print(f"{solution['input_rate']} {unit}/min input rate")
            print(f"{solution['platform_rate']} {unit}/min active platform rate")
            efficiency = (
                solution["throughput"]
                / solution["platform_rate"]
                / solution["cars"]
                * 100
            )
            print(
                f"{round(solution['throughput'], 4)} {unit}/min throughput ({round(efficiency, 2)}% platform efficiency)"
            )
            if args.input_rate:
                ratio = solution["output_rate"] / solution["input_rate"] * 100
                print(
                    f"{round(solution['output_rate'], 4)} {unit}/min output rate ({round(ratio, 2)}% of input)"
                )

            # If the input buffer isn't the same as the output buffer, the input
            # rate must be larger than the throughput and it will be useless.
            if solution["input_buffer"] == solution["output_buffer"]:
                buffer_label = "buffers"
            else:
                print("input buffer would be saturated and useless")
                buffer_label = "output buffer"
            buffer_size = round(solution["output_buffer"]["size"], 2)
            buffer_time = fmt_time(solution["output_buffer"]["time"])
            print(
                f"{buffer_size} {unit} in {buffer_label}, empties {buffer_time} after (un)load"
            )
        else:
            print("No solution found.")

    except ValueError as e:
        print(f"Error: {e}")
