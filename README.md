# SAT is Factory

SAT solving for Satisfactory.

Consistent with https://satisfactory.wiki.gg/wiki/Tutorial:Train_throughput, but
works with multiple trains and cars. See [the unit
test](https://github.com/nixpulvis/sat_is_factory/blob/c66a67b8290bca102d4e243adf7c6d995ff53ef5/tests/test_train_solver.py#L76)
which verifies this.

For more information read the `--help` message.

### Setup

```sh
# Setup a venv (optional)
python3 -m venv .venv
source .venv/bin/activate # add .fish for fish shell.
pip3 install --editable .
```

### Usage

```sh
$ python3 -m sat_is_factory.train_solver --help

usage: python3 -m sat_is_factory.train_solver [-h] [--stack STACK] [--belt BELT] [--pipe [PIPE]] [--trains TRAINS] [--max-trains MAX_TRAINS] [--cars CARS]
                                              [--max-cars MAX_CARS] [--minimize MINIMIZE] [--rtd RTD] [--throughput THROUGHPUT]
...
```

### Examples

```sh
# Solve for trains and cars needed given a fixed RtD and needed throughput.
$ python3 -m sat_is_factory.train_solver --rtd 9 --throughput 3000

minimize cars, minimize trains, minimize throughput >= 3000.0
Stack Size: 100
Belt Speed: 1200
Trains: 5
Cars: 2
Loaded: full
Round Trip Time: 9.0 min (540.0 sec)
Throughput: 3555.5556 items/min

# Solve for optimal RtD and throughput.
$ python3 -m sat_is_factory.train_solver --stack 500 --belt 780

minimize cars, minimize trains, minimize rtd, solving optimal throughput
Stack Size: 500
Belt Speed: 780
Trains: 1
Cars: 1
Loaded: full
Round Trip Time: 10.7077 min (642.46 sec)
Throughput: 1494.2457 items/min
```

### Testing

```sh
python3 -m unittest
python3 -m unittest tests.test_train_solver.TestMaximizingThroughput.test_max_multiple_trains
