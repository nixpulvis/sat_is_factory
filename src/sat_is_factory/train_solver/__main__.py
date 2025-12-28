import argparse
import re

from sat_is_factory.train_solver import TrainSolver


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
This program can be used to solve the train throughput equations for single or
multi train/car setups.

Depending on the input flags, the program will either:

- Solve the optimal RtD and throughput, when neither are provided
- Minimize the system while achieving a given throughput
- Maximize the throughput for a given RtD

Take note of the default values, which assume common stack sizes of 100 and
maximum belt speeds of 1,200 items/min. There are also somewhat reasonable
default maximum values for the number of trains and cars per train.

Use the `--minimize trains` flag if you wish to solve for routes with fewer
trains while increasing the number of cars per train.

For results with more than one train, it is assumed that they are evenly spaced
and doing so is up to you to implement correctly in-game. If the result calls
for fully loaded trains, one method to achive this to set the train to wait
until it's fully loaded/unloaded AND 0 seconds. A more generic method, if the
train is partially loaded, or carrying other items, is to set the train to wait
until one load/unload AND `RtD / number of trains` (TODO: test this).

For pipes, use --stack 50 and --belt=<flowrate>
""",
        formatter_class=Formatter,
    )

    constants = parser.add_argument_group("constants")
    constants.add_argument("--stack", type=int, default=100, help="Item stack quantity")
    constants.add_argument("--belt", type=int, default=1200, help="Belt speed")
    constants.add_argument(
        "--pipe",
        type=int,
        nargs="?",
        const=600,
        help="Pipe speed (sets --stack to 50)",
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

    if args.pipe:
        args.stack = 50
        args.dock_speed = args.pipe
    else:
        args.dock_speed = args.belt

    try:
        solver = TrainSolver(args)
        print(", ".join(solver.info))

        solution = solver.solve()
        if solution is not None:
            if args.pipe is None:
                print(f"Stack Size: {solution['stack']} items")
                print(f"Belt Speed: {solution['dock_speed']} items/min")
            else:
                print(f"Flow Rate: {solution['dock_speed']} m^3/min")

            print(f"Trains: {solution['trains']}")
            print(f"Cars: {solution['cars']}")
            print(f"Loaded: {solution['loaded']}")
            print(
                f"Round Trip Time: {round(solution['rtd'], 4)} min ({round(solution['rtd'] * 60, 2)} sec)"
            )
            efficency = (
                solution["throughput"]
                / solution["dock_speed"]
                / 2
                / solution["cars"]
                * 100
            )
            print(
                f"Throughput: {round(solution['throughput'], 4)} items/min ({round(efficency, 2)}%)"
            )
        else:
            print("No solution found.")

    except ValueError as e:
        print(f"Error: {e}")
