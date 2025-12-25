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
python3 -m sat_is_factory.train_solver --help
python3 -m sat_is_factory.train_solver --stack 500 --belt 780
python3 -m sat_is_factory.train_solver --stack 100 --belt 1200 --rtd 9 --throughput 3000
```

### Testing

```sh
python3 -m unittest
python3 -m unittest tests.test_train_solver.TestMaximizingThroughput.test_max_multiple_trains
