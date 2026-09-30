import os
import random
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from bopit import screens
from bopit.app import App
from bopit.config import Settings
from bopit.engine import events as ev
from bopit.engine.game import BEAT, Game, Options, State, tutorial_rules
from bopit.menu import Nav
from bopit.progress import Progress
from bopit.savegame import SavedGame
from bopit.scores import Scores
from bopit.tutorials import TUTORIAL_ORDER, tutorial_text
from tests.test_screens import FakeNavigator, labels


class TutorialEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(tutorial_rules("Twist"), Options(), random.Random(4), {})
        self.game.prepare(0.0)
        self.game.press("Bop", 1.0)          # How GameScreen starts it at once.
        self.game.pop_events()

    def open_turn(self) -> float:
        while self.game.state != State.IN_TURN:
            self.game.update(self.game._timers[0][0])
        return self.game.turn_opened_at

    def test_only_the_featured_command(self) -> None:
        self.assertEqual(self.game.active, ["Twist"])
        for _ in range(20):
            now = self.open_turn()
            self.assertEqual(self.game.current, "Twist")
            self.game.press("Twist", now + 0.2)
        self.assertEqual(self.game.pitch, 1.0)

    def test_mistakes_do_not_end_it(self) -> None:
        now = self.open_turn()
        self.game.press("Bop", now + 0.2)
        events = self.game.pop_events()
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertFalse(any(isinstance(e, (ev.HelpNeeded, ev.GameOver)) for e in events))
        self.assertEqual(self.game._timers[0][0], now + 0.2 + BEAT)
        now = self.open_turn()
        self.game.update(now + 5.0)            # A timeout goes on too.
        self.assertNotEqual(self.game.state, State.OVER)

    def test_stop(self) -> None:
        now = self.open_turn()
        self.game.stop(now + 0.1)
        self.assertEqual(self.game.state, State.OVER)
        self.assertEqual(self.game._timers, [])
        self.assertIn(ev.MusicStop(), self.game.pop_events())


class TutorialTextTests(unittest.TestCase):
    def test_name_and_key(self) -> None:
        self.assertEqual(tutorial_text("Twist"), "Twist It: press Left.")
        self.assertEqual(tutorial_text("Bop"), "Bop It: press Space.")

    def test_shout_keeps_its_x_move(self) -> None:
        self.assertIn("microphone for an X-Move Bonus!", tutorial_text("Shout"))
        self.assertEqual(tutorial_text("Shout", microphone=False), "Shout It: press Y.")


class TutorialMenuTests(unittest.TestCase):
    def test_all_twelve_in_grid_order(self) -> None:
        nav = FakeNavigator()
        opened: list[str] = []
        nav.open_tutorial = opened.append
        menu = screens.tutorials_menu(nav)
        self.assertEqual(labels(menu), list(TUTORIAL_ORDER))
        self.assertEqual(TUTORIAL_ORDER[:4], ("Bop", "Twist", "Pull", "Spin"))
        menu.handle(Nav.LAST, _Quiet(), nav.play_themed)
        menu.handle(Nav.SELECT, _Quiet(), nav.play_themed)
        self.assertEqual(opened, ["Poke"])
        self.assertEqual(nav.played, [])     # The buttons made no sound.


class _Quiet:
    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None:
        pass


class _Speaker:
    def __init__(self) -> None:
        self.said: list[str] = []

    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None:
        self.said.append(text)


class _Audio:
    def play(self, name: str, **kw: object) -> None:
        return None


class TutorialFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        tmp = Path(tempfile.mkdtemp())
        self.speech = _Speaker()
        self.app = App(self.speech, _Audio(), Settings())
        self.app.scores = Scores(tmp / "scores.json")
        self.app.progress = Progress(tmp / "progress.json")
        self.app.saved_game = SavedGame(tmp / "savegame.json")
        self.app.push(screens.main_menu(self.app))
        self.now = time.perf_counter()

    def titles(self) -> list[str]:
        return [s.title for s in self.app._stack]

    def test_first_game_asks_once(self) -> None:
        self.app.start_mode("Classic")
        self.assertEqual(self.titles()[-1], screens.TUTORIAL_POPUP_QUESTION)
        self.app.leave_game()
        self.app.start_mode("Classic")
        self.assertEqual(self.titles()[-1], "Classic")

    def test_back_from_tutorial_goes_to_list_without_a_mode(self) -> None:
        self.app.push(screens.tutorials_menu(self.app))
        self.app.open_tutorial("Nail")
        self.app.tutorial_back()
        self.assertEqual(self.titles()[-1], "Tutorials")

    def test_back_from_tutorial_goes_into_the_mode(self) -> None:
        self.app.progress.first_time("tutorial_popup")
        self.app.start_mode("Basic")
        self.app.try_tutorial("Twist")
        self.assertEqual(self.titles(), ["Bop It", "Options", "Help", "Tutorials",
                                         "Twist tutorial"])
        self.app.tutorial_back()
        self.assertEqual(self.titles(), ["Bop It", "Basic"])

    def test_end_screen_menu_forgets_the_mode(self) -> None:
        self.app.progress.first_time("tutorial_popup")
        self.app.start_mode("Basic")
        self.app.leave_game()
        self.assertIsNone(self.app.tutorial_return)


if __name__ == "__main__":
    unittest.main()
