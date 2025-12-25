# SAT is Factory

SAT solving for Satisfactory.

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

usage: python3 -m sat_is_factory.train_solver [-h] [--stack STACK] [--belt BELT] [--rtd RTD]
                                              [--max-trains MAX_TRAINS] [--trains TRAINS] [--max-cars MAX_CARS]
                                              [--cars CARS] [--throughput THROUGHPUT] [--minimize MINIMIZE]

For pipes, use --stack 50 and --belt=<flowrate>

options:
  -h, --help            show this help message and exit
  --stack STACK         Item stack quantity (default: 100)
  --belt BELT           Belt speed (default: 1200)
  --rtd RTD             Round trip time, otherwise optimized for (default: None)
  --max-trains MAX_TRAINS
                        Max number of trains (default: None)
  --trains TRAINS       Number of trains (default: None)
  --max-cars MAX_CARS   Max number of cars (default: None)
  --cars CARS           Number of cars (default: None)
  --throughput THROUGHPUT
                        Min throughput needed (default: None)
  --minimize MINIMIZE   Prioritize minimizing either trains, cars (default: None)
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
