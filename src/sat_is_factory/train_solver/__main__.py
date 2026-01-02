import argparse
import math

from sat_is_factory.train_solver import TrainSolver
from sat_is_factory.train_solver.train_solver import CAR_CAPACITY
from sat_is_factory.util import fmt_time, pluralize, time

HELP = """
This program can be used to solve the train throughput equations for single or
multi train/car setups.

Depending on the input flags, the program will either:

- Solve the optimal RTD and throughput, when neither are provided
- Minimize the system while achieving a given throughput
- Maximize the throughput for a given RTD

RTD is the Round Trip Duration for any one specific train. This is most easily
measured by timing the duration of a train from "toot-to-toot". If there is
congestion on the tracks, then an average should be used for closest results.

The source argument allows directly calculating an available output rate as well
as source platform(s) buffer information. The sink option further allows
ensuring a final consistent rate to downstream consumers of the unloading
platform(s). These calculations assume each platform has the same platform rate
and that the source and sink are properly balanced. Balancing train stations is
sometimes needed to achieve maximum throughput when using the wait until fully
loaded/unloaded option in game.

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


STACK_SENTINAL = object()
PLATFORM_SENTINAL = object()


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
        help="Platform loading speed (sum of belt/pipe speeds)",
    )
    constants.add_argument(
        "--fluid",
        action="store_true",
        help="Using fluids (sets --stack to 50)",
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
    if args.sink_rate is not None and args.source_rate is None:
        parser.error("--source is required when --sink is provided")

    set_additional_defaults(parser, args)
    return args


def set_additional_defaults(parser, args):
    if args.fluid:
        if args.stack == STACK_SENTINAL:
            args.stack = 1600 / CAR_CAPACITY
        else:
            parser.error("cannot use --stack with --fluid")
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = 1200
    else:
        if args.stack == STACK_SENTINAL:
            args.stack = 100
        if args.platform_rate == PLATFORM_SENTINAL:
            args.platform_rate = 2400


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
        f"{loaded_kind} with {round(solution['loaded'])} {unit} ({pluralize('stack', stacks)})",
        end="",
    )
    if (
        "source" in solution
        and "sink" in solution
        and solution["source"]["rate"] > solution["sink"]["rate"]
    ):
        print(", not fully unloaded", end="")
    print()
    print(f"{fmt_time(solution['rtd'])} per round trip.")


def print_station_solution(solution, unit):
    print(f"{solution['platform_rate']} {unit}/min active platform rate")
    efficiency = (
        solution["throughput"] / solution["platform_rate"] / solution["cars"] * 100
    )
    print(
        f"{round(solution['throughput'], 4)} {unit}/min throughput ({round(efficiency, 2)}% platform efficiency)"
    )


def print_io_solution(solution, unit):
    def print_buffer_solution(key, solution, unit):
        buffer_size = math.ceil(solution[key]["buffer"]["size"])
        buffer_time = fmt_time(solution[key]["buffer"]["time"])
        if key == "source":
            verb = "empties"
            action = "load"
        else:
            verb = "fills"
            action = "unload"
        buffer = pluralize(f"{key} buffer", solution["cars"], name_only=True)
        print(f"{buffer_size} {unit} in {buffer}, {verb} {buffer_time} after {action}")

    if "source" in solution:
        print(f"{round(solution['source']['rate'], 4)} {unit}/min source rate")
        if (
            "sink" in solution
            and solution["source"]["rate"] <= solution["sink"]["rate"]
        ):
            print_buffer_solution("source", solution, unit)
        ratio = solution["available_rate"] / solution["source"]["rate"] * 100
        print(
            f"{round(solution['available_rate'], 4)} {unit}/min available output rate ({round(ratio, 2)}% of source)"
        )
    if "sink" in solution:
        print(f"{round(solution['sink']['rate'], 4)} {unit}/min sink rate")
        print_buffer_solution("sink", solution, unit)


if __name__ == "__main__":
    main()
