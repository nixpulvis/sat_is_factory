# SAT is Factory

SAT solving for Satisfactory.

Using Python with [`z3-solver`](https://pypi.org/project/z3-solver/) for
[Z3](https://github.com/Z3Prover/z3).

## `train-solver`

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

<details>
<summary>Optionally set up a virtual environment (venv) first, then install
inside the venv.</summary>

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
</details>

### Usage

```
usage: train-solver [-h]
  [--stack STACK]
  [--platform PLATFORM_RATE] [--fluid]
  [--trains TRAINS] [--max-trains MAX_TRAINS] [--cars CARS] [--max-cars MAX_CARS] [--minimize MINIMIZE]
  [--rtd RTD] [--throughput THROUGHPUT]
  [--source SOURCE_RATE] [--sink SINK_RATE]
```

### Examples

Solve for trains and cars needed given a fixed RTD and needed throughput.
```sh
$ train-solver --rtd 9 --throughput 3000
minimize cars, minimize trains, minimize throughput >= 3000.0

5 trains
2 cars
full with 3200 items (32 stacks)
9 min 0.0 sec per round trip.
4800 items/min total active rate of platforms
3555.5556 items/min throughput (74.07% platform efficiency)
```

Solve for optimal RTD and throughput.
```sh
$ train-solver --stack 500 --platform 1560
minimize cars, minimize trains, minimize rtd, optimal

1 train
1 car
full with 16000 items (32 stacks)
10 min 42.46 sec per round trip.
1560 items/min total active rate of platform
1494.2457 items/min throughput (95.78% platform efficiency)
```

Solve with source and sink rates.
```sh
$ train-solver --platform 960 --source 800 --sink 600 --rtd 5
minimize cars, minimize trains, minimize throughput >= 800.0

1 train
2 cars
partially filled with 2000 items (20 stacks), not fully unloaded
5 min 0.0 sec per round trip.
1920 items/min total active rate of platforms
1280.0 items/min throughput (66.67% platform efficiency)

800.0 items/min source rate (62.5% of throughput)
source buffer would eventually be full
800.0 items/min available
600.0 items/min sink rate (75.0% of available)
136 items in sink buffers fills after 12.31 sec
```

### Testing

```sh
python3 -m unittest
python3 -m unittest tests.test_train_solver.TestMaximizingThroughput.test_max_multiple_trains
```
