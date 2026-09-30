import copy
import json
import tempfile
import unittest
from pathlib import Path

import pygame

from bopit import input_map
from bopit.input_map import DEFAULTS, build, load_bindings


class BuildTests(unittest.TestCase):
    def test_defaults_have_no_problems(self) -> None:
        bindings, problems = build(DEFAULTS)
        self.assertEqual(problems, [])
        self.assertEqual(bindings.game[pygame.K_SPACE], "Bop")
        self.assertEqual(bindings.game[pygame.K_LEFT], "Twist")
        self.assertEqual(bindings.pause, {pygame.K_ESCAPE})
        self.assertEqual(bindings.h2h[pygame.K_f], (0, None))
        self.assertEqual(bindings.h2h[pygame.K_s], (0, 1))
        self.assertEqual(bindings.h2h_score, {pygame.K_TAB})

    def test_missing_entries_use_defaults(self) -> None:
        bindings, problems = build({"game": {"Bop": ["b"], "Brush": ["x"]}})
        self.assertEqual(problems, [])
        self.assertEqual(bindings.game[pygame.K_b], "Bop")
        self.assertEqual(bindings.game[pygame.K_x], "Brush")
        self.assertEqual(bindings.game[pygame.K_LEFT], "Twist")

    def test_several_keys_and_a_single_string(self) -> None:
        bindings, _ = build({"game": {"Bop": ["space", "return"]}, "score": "tab"})
        self.assertEqual(bindings.game[pygame.K_RETURN], "Bop")
        self.assertEqual(bindings.game[pygame.K_SPACE], "Bop")
        self.assertEqual(bindings.score, {pygame.K_TAB})

    def test_unknown_key_name_falls_back(self) -> None:
        bindings, problems = build({"game": {"Twist": ["banana"]}})
        self.assertEqual(bindings.game[pygame.K_LEFT], "Twist")
        self.assertEqual(len(problems), 1)
        self.assertIn("banana", problems[0])

    def test_unknown_names_reported(self) -> None:
        _, problems = build({"game": {"Wiggle": ["w"]}, "extra": 1})
        self.assertEqual(len(problems), 2)

    def test_conflict_keeps_first(self) -> None:
        bindings, problems = build({"game": {"Twist": ["escape"]}})
        self.assertIn(pygame.K_ESCAPE, bindings.pause)
        self.assertNotIn(pygame.K_ESCAPE, bindings.game)
        self.assertEqual(len(problems), 1)
        self.assertIn("pause", problems[0])

    def test_pause_can_never_be_empty(self) -> None:
        bindings, _ = build({"pause": ["s"], "score": ["s"]})
        self.assertEqual(bindings.pause, {pygame.K_s})
        self.assertNotIn(pygame.K_s, bindings.score)

    def test_head_to_head_separate_from_solo(self) -> None:
        # S is the solo score key and Green's second command; that is fine.
        data = copy.deepcopy(DEFAULTS)
        _, problems = build(data)
        self.assertEqual(problems, [])


class LoadTests(unittest.TestCase):
    def tearDown(self) -> None:
        input_map._current, _ = build(DEFAULTS)

    def test_writes_defaults_when_missing(self) -> None:
        path = Path(tempfile.mkdtemp()) / "keys.json"
        self.assertEqual(load_bindings(path), [])
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), DEFAULTS)

    def test_broken_file_uses_defaults_and_is_kept(self) -> None:
        path = Path(tempfile.mkdtemp()) / "keys.json"
        path.write_text("{not json", encoding="utf-8")
        problems = load_bindings(path)
        self.assertEqual(len(problems), 1)
        self.assertEqual(path.read_text(encoding="utf-8"), "{not json")
        self.assertEqual(input_map.game_command_for(pygame.K_SPACE), "Bop")

    def test_loaded_keys_take_effect(self) -> None:
        path = Path(tempfile.mkdtemp()) / "keys.json"
        path.write_text(json.dumps({"game": {"Bop": ["x"]}}), encoding="utf-8")
        load_bindings(path)
        self.assertEqual(input_map.game_command_for(pygame.K_x), "Bop")
        self.assertIsNone(input_map.game_command_for(pygame.K_SPACE))
        self.assertEqual(input_map.key_name_for("Bop"), "X")

    def test_help_lines(self) -> None:
        lines = input_map.describe_bindings()
        self.assertEqual(lines[0], "Bop: Space")
        self.assertIn("Head 2 Head Green: Bop F, first command D, second command S", lines)


if __name__ == "__main__":
    unittest.main()
