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
