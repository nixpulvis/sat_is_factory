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
  [--stack STACK] [--belt BELT] [--pipe [PIPE]]
  [--trains TRAINS] [--max-trains MAX_TRAINS] [--cars CARS] [--max-cars MAX_CARS] [--minimize MINIMIZE]
  [--rtd RTD] [--throughput THROUGHPUT]
```

### Examples

Solve for trains and cars needed given a fixed RtD and needed throughput.
```sh
$ python3 -m sat_is_factory.train_solver --rtd 9 --throughput 3000

minimize cars, minimize trains, minimize throughput >= 3000.0
Stack Size: 100 items
Belt Speed: 1200 items/min
Trains: 5
Cars: 2
Loaded: full
Round Trip Time: 9.0 min (540.0 sec)
Throughput: 3555.5556 items/min (74.07%)
```

Solve for optimal RtD and throughput.
```sh
$ python3 -m sat_is_factory.train_solver --stack 500 --belt 780

minimize cars, minimize trains, minimize rtd, solving optimal
Stack Size: 500 items
Belt Speed: 780 items/min
Trains: 1
Cars: 1
Loaded: full
Round Trip Time: 10.7077 min (642.46 sec)
Throughput: 1494.2457 items/min (95.78%)
```

### Testing

```sh
python3 -m unittest
python3 -m unittest tests.test_train_solver.TestMaximizingThroughput.test_max_multiple_trains
```
