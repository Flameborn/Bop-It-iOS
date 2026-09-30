import tempfile
import unittest
from pathlib import Path

from bopit.scores import Entry, Scores


class ScoresTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "scores.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_new_mode_has_placeholder(self) -> None:
        self.assertEqual(Scores(self.path).entries("Classic"), [Entry(0, 0)])

    def test_add_returns_previous_best_and_sorts(self) -> None:
        scores = Scores(self.path)
        self.assertEqual(scores.add("Classic", 500, 5), 0)
        self.assertEqual(scores.add("Classic", 300, 3), 500)
        self.assertEqual(scores.add("Classic", 900, 9), 500)
        self.assertEqual([e.score for e in scores.entries("Classic")], [900, 500, 300, 0])

    def test_tie_goes_above(self) -> None:
        scores = Scores(self.path)
        scores.add("Classic", 500, 5)
        scores.add("Classic", 500, 6)
        self.assertEqual(scores.entries("Classic")[0], Entry(500, 6))

    def test_list_is_cut_to_ten(self) -> None:
        scores = Scores(self.path)
        for n in range(1, 13):
            scores.add("Classic", n * 10, n)
        entries = scores.entries("Classic")
        self.assertEqual(len(entries), 10)
        self.assertEqual(entries[0].score, 120)

    def test_saved_and_reloaded(self) -> None:
        Scores(self.path).add("Classic", 700, 7)
        self.assertEqual(Scores(self.path).best("Classic"), Entry(700, 7))


if __name__ == "__main__":
    unittest.main()


class BlitzTimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.scores = Scores(Path(self.tmp.name) / "scores.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def times(self) -> list[float]:
        return [e.score for e in self.scores.entries("Blitz")]

    def test_first_time_is_new_best(self) -> None:
        self.assertEqual(self.scores.add_time("Blitz", 25.0), 0)
        self.assertEqual(self.times(), [25.0, 0])

    def test_fastest_first_with_placeholder_last(self) -> None:
        for t in (25.0, 20.0, 22.0, 30.0):
            self.scores.add_time("Blitz", t)
        self.assertEqual(self.times(), [20.0, 22.0, 25.0, 30.0, 0])

    def test_new_best_only_when_faster(self) -> None:
        self.scores.add_time("Blitz", 20.0)
        self.scores.add_time("Blitz", 25.0)
        self.assertLess(18.0, self.scores.add_time("Blitz", 18.0))
        self.assertFalse(22.0 < self.scores.add_time("Blitz", 22.0))
        self.assertFalse(18.0 < self.scores.add_time("Blitz", 18.0))

    def test_full_list_drops_slow_times(self) -> None:
        for n in range(12):
            self.scores.add_time("Blitz", 10.0 + n)
        times = self.times()
        self.assertEqual(len(times), 10)
        self.assertEqual(times[0], 10.0)
        self.assertNotIn(0, times)
        self.scores.add_time("Blitz", 50.0)
        self.assertNotIn(50.0, self.times())
