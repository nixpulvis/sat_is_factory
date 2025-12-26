import unittest

from sat_is_factory.train_solver import TrainSolver


class TestArgs:
    def __init__(self, dict):
        self.stack = None
        self.dock_speed = None
        self.trains = None
        self.max_trains = None
        self.cars = None
        self.max_cars = None
        self.rtd = None
        self.throughput = None
        self.minimize = None
        for key, value in dict.items():
            setattr(self, key, value)


# Solves for optimal RtD and Throughput when neither is provided.
class TestOptimal(unittest.TestCase):
    def test_single_train(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 1,
                    "cars": 1,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 1.7847, places=4)
        self.assertAlmostEqual(solution["throughput"], 1793.0519, places=4)

    # Solves for optimal RtD and Throughput when neither is provided.
    def test_multiple_train(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 2,
                    "cars": 1,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 1.7847 * 2, places=3)
        self.assertAlmostEqual(solution["throughput"], 1793.0519, places=4)

    def test_multiple_car(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 1,
                    "cars": 2,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 1.7847, places=4)
        self.assertAlmostEqual(solution["throughput"], 1793.0519 * 2, places=3)

    # Test values from https://satisfactory.wiki.gg/wiki/Tutorial:Train_throughput
    def test_wiki(self):
        cases = [
            {
                "stack": 50,
                "dock_speed": 780,
                "rtd": 88.62 / 60,
                "throughput": 1083.3,
            },
            {
                "stack": 50,
                "dock_speed": 1200,
                "rtd": 67.08 / 60,
                "throughput": 1431.17,
            },
            {
                "stack": 100,
                "dock_speed": 780,
                "rtd": 150.16 / 60,
                "throughput": 1278.66,
            },
            {
                "stack": 100,
                "dock_speed": 1200,
                "rtd": 102.08 / 60,
                "throughput": 1793.08,
            },
            {
                "stack": 200,
                "dock_speed": 780,
                "rtd": 273.23 / 60,
                "throughput": 1405.4,
            },
            {
                "stack": 200,
                "dock_speed": 1200,
                "rtd": 187.08 / 60,
                "throughput": 2052.62,
            },
            {
                "stack": 500,
                "dock_speed": 780,
                "rtd": 642.46 / 60,
                "throughput": 1494.25,
            },
            {
                "stack": 500,
                "dock_speed": 1200,
                "rtd": 427.08 / 60,
                "throughput": 2247.83,
            },
            {
                "stack": 50,
                "dock_speed": 600,
                "rtd": 107.08 / 60,
                "throughput": 896.52,
            },
        ]
        for case in cases:
            solver = TrainSolver(
                TestArgs({k: case[k] for k in ["stack", "dock_speed"] if k in case})
            )
            solution = solver.solve()
            self.assertIsNotNone(solution)
            self.assertEqual(solution["loaded"], "full")
            self.assertAlmostEqual(solution["rtd"], case["rtd"], delta=0.5)
            self.assertAlmostEqual(solution["throughput"], case["throughput"], delta=1)


# Minimizing to get >= throughput
class TestMinimizingThroughput(unittest.TestCase):
    def test_many_trains_and_cars(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "rtd": 9,
                    "throughput": 3000,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["trains"], 5)
        self.assertEqual(solution["cars"], 2)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 9, places=4)
        self.assertAlmostEqual(solution["throughput"], 3555.5556, places=4)

    def test_many_trains_and_cars_minimize_trains(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "rtd": 9,
                    "throughput": 3000,
                    "minimize": "trains",
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["trains"], 1)
        self.assertEqual(solution["cars"], 9)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 9, places=4)
        self.assertAlmostEqual(solution["throughput"], 3200, places=4)

    def test_many_trains_and_max_cars_minimizing_trains(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "rtd": 9,
                    "throughput": 3000,
                    "max_cars": 4,
                    "minimize": "trains",
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["trains"], 3)
        self.assertEqual(solution["cars"], 3)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 9, places=4)
        self.assertAlmostEqual(solution["throughput"], 3200, places=4)

    def test_many_max_trains_and_cars(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "rtd": 13,
                    "throughput": 3000,
                    "max_trains": 2,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["trains"], 2)
        self.assertEqual(solution["cars"], 7)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["rtd"], 13, places=4)
        self.assertAlmostEqual(solution["throughput"], 3446.1538, places=4)

    # TODO: Also not sure why this test is hanging when run with all the other tests.
    @unittest.skip("TODO: figure out if we can make this consistent")
    def test_cars_effects_rtd(self):
        params = {
            "stack": 100,
            "dock_speed": 1200,
            "trains": 1,
            "throughput": 1000.0,
        }
        solver_a = TrainSolver(TestArgs(params))
        solution_a = solver_a.solve()
        solver_b = TrainSolver(TestArgs({**params, "cars": 1}))
        solution_b = solver_b.solve()
        self.assertEqual(solution_a, solution_b)


# Maximizing throughput for a given RtD.
class TestMaximizingThroughput(unittest.TestCase):
    def test_max_is_partial(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 1,
                    "cars": 1,
                    "rtd": 1.65,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "partial")
        self.assertAlmostEqual(solution["throughput"], 1743.5152, places=4)

    def test_max_is_full(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 1,
                    "cars": 1,
                    "rtd": 1.95,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "full")
        self.assertAlmostEqual(solution["throughput"], 1641.0256, places=4)

    def test_max_multiple_trains(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 2,
                    "cars": 1,
                    "rtd": 1.95,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "partial")
        self.assertAlmostEqual(solution["throughput"], 1289.0256, places=4)

    def test_max_multiple_cars(self):
        solver = TrainSolver(
            TestArgs(
                {
                    "stack": 100,
                    "dock_speed": 1200,
                    "trains": 2,
                    "cars": 2,
                    "rtd": 1.95,
                }
            )
        )
        solution = solver.solve()
        self.assertIsNotNone(solution)
        self.assertEqual(solution["loaded"], "partial")
        self.assertAlmostEqual(solution["throughput"], 1289.0256 * 2, places=3)


if __name__ == "__main__":
    unittest.main()
