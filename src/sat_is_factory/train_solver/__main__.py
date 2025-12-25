import argparse

from sat_is_factory.train_solver import TrainSolver

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
    parser.add_argument(
        "--minimize",
        type=str,
        help="Prioritize minimizing either trains, cars",
    )

    args = parser.parse_args()

    try:
        solver = TrainSolver(args)
        print(", ".join(solver.info))
        solution = solver.solve()

        if solution is not None:
            print(f"Stack Size: {solution['stack']}")
            print(f"Belt Speed: {solution['belt']}")
            print(f"Trains: {solution['trains']}")
            print(f"Cars: {solution['cars']}")
            print(f"Loaded: {solution['loaded']}")
            print(
                f"Round Trip Time: {round(solution['rtd'], 4)} min ({round(solution['rtd'] * 60, 2)} sec)"
            )
            print(f"Throughput: {round(solution['throughput'], 4)} items/min")
        else:
            print("No solution found.")

    except ValueError as e:
        print(f"Error: {e}")
