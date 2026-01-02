# SAT is Factory

SAT solving for Satisfactory.

Using Python with [`z3-solver`](https://pypi.org/project/z3-solver/) for
[Z3](https://github.com/Z3Prover/z3).

## `train_solver`

Consistent with https://satisfactory.wiki.gg/wiki/Tutorial:Train_throughput, but
works with multiple trains and cars. See [the unit
test](https://github.com/nixpulvis/sat_is_factory/blob/c66a67b8290bca102d4e243adf7c6d995ff53ef5/tests/test_train_solver.py#L76)
which verifies this.

For more information read the `--help` message.

### Setup

Install the package.

```sh
pip3 install .
# Use `--editable` if you plan to edit this package.
```

Optionally set up a virtual environment (venv) first, then install inside the
venv.

```sh
python3 -m venv .venv

# Bash
source .venv/bin/activate 
# Fish
source .venv/bin/activate.fish
# CMD (Windows)
.\.venv\Scripts\activate
# PowerShell (Windows)
.\.venv\Scripts\activate.ps1
```

### Usage

```
usage: python3 -m sat_is_factory.train_solver [-h]
  [--stack STACK]
  [--platform PLATFORM_RATE] [--fluid] [--input INPUT_RATE]
  [--trains TRAINS] [--max-trains MAX_TRAINS] [--cars CARS] [--max-cars MAX_CARS] [--minimize MINIMIZE]
  [--rtd RTD] [--throughput THROUGHPUT]
```

### Examples

Solve for trains and cars needed given a fixed RtD and needed throughput.
```sh
$ python3 -m sat_is_factory.train_solver --rtd 9 --throughput 3000
minimize cars, minimize trains, minimize throughput >= 3000.0

5 trains
2 cars
full with 3200 items (32 stacks)
9 min 0.0 sec per round trip.
2400 items/min active platform rate
3555.5556 items/min throughput (74.07% platform efficiency)
```

Solve for optimal RtD and throughput.
```sh
$ python3 -m sat_is_factory.train_solver --stack 500 --belt 780
minimize cars, minimize trains, minimize rtd, optimal

1 train
1 car
full with 16000 items (32 stacks)
10 min 42.46 sec per round trip.
1560 items/min active platform rate
1494.2457 items/min throughput (95.78% platform efficiency)
```

### Testing

```sh
python3 -m unittest
python3 -m unittest tests.test_train_solver.TestMaximizingThroughput.test_max_multiple_trains
```
