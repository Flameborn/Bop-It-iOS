import tempfile
import unittest
from pathlib import Path

from bopit.progress import Progress


class ProgressTests(unittest.TestCase):
    def test_message_only_first_time_and_saved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            progress = Progress(path)
            self.assertEqual(progress.unlock("Spin"), "Spin to Win! Spin Unlocked")
            self.assertIsNone(progress.unlock("Spin"))
            self.assertIsNone(Progress(path).unlock("Spin"))

    def test_no_message_for_commands_without_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(Progress(Path(tmp) / "p.json").unlock("Twist"))


if __name__ == "__main__":
    unittest.main()
