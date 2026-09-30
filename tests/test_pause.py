import json
import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import BASIC, BLITZ, CLASSIC, Game, Options, State


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


def started(rules, seed: int = 2) -> Game:
    game = Game(rules, Options(), random.Random(seed))
    game.prepare(0.0)
    game.press("Bop", 0.0)
    game.pop_events()
    return game


def win(game: Game, count: int) -> float:
    now = 0.0
    for _ in range(count):
        now = game._timers[0][0]
        game.update(now)
        game.press(game.current or "", now + 0.1)
    game.pop_events()
    return now + 0.1


class PauseTests(unittest.TestCase):
    def test_pause_stops_turn_and_music(self) -> None:
        game = started(CLASSIC)
        now = win(game, 3)
        game.pause(now + 0.2)
        self.assertEqual(game.state, State.PAUSED)
        self.assertIn(ev.MusicStop(), game.pop_events())
        game.update(now + 100)
        self.assertEqual(game.state, State.PAUSED)

    def test_resume_calls_new_command_and_opens_turn_a_beat_later(self) -> None:
        game = started(CLASSIC)
        now = win(game, 3)
        game.pause(now + 0.2)
        game.pop_events()
        game.resume(50.0)
        events = game.pop_events()
        self.assertEqual(len(of(events, ev.CommandCalled)), 1)
        self.assertIn(ev.MusicStart("MUSIC_GameLoop_01a", 1.0, 1.62), events)
        self.assertAlmostEqual(game._timers[0][0], 50.81)
        self.assertEqual(game.moves, 3)

    def test_cannot_pause_after_failing(self) -> None:
        game = started(CLASSIC)
        now = game._timers[0][0]
        game.update(now + 1.1)
        game.pause(now + 1.2)
        self.assertNotEqual(game.state, State.PAUSED)

    def test_blitz_clock_stops_while_paused(self) -> None:
        game = started(BLITZ)
        now = win(game, 2)
        elapsed = game.blitz_elapsed(now)
        game.pause(now)
        game.resume(now + 30)
        self.assertAlmostEqual(game.blitz_elapsed(now + 30), elapsed)

    def test_save_and_load(self) -> None:
        game = started(BASIC)
        now = win(game, 20)
        game.pause(now)
        data = json.loads(json.dumps(game.save()))
        loaded = Game(BASIC, Options(), random.Random(9))
        loaded.load(data, 100.0)
        self.assertEqual(loaded.state, State.PAUSED)
        self.assertEqual((loaded.moves, loaded.bonus, loaded.active, loaded.pitch),
                         (game.moves, game.bonus, game.active, game.pitch))
        loaded.resume(100.0)
        opened = loaded._timers[0][0]
        loaded.update(opened)
        loaded.press(loaded.current or "", opened + 0.1)
        self.assertEqual(loaded.moves, 21)


if __name__ == "__main__":
    unittest.main()
