import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import BLITZ, Game, Options, State


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class BlitzTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(BLITZ, Options(), random.Random(5))
        self.game.prepare(0.0)
        self.game.press("Bop", 10.0)
        self.events: list[ev.Event] = self.game.pop_events()

    def next_turn(self) -> float:
        now = self.game._timers[0][0]
        self.game.update(now)
        self.events += self.game.pop_events()
        return now

    def press(self, command: str, when: float) -> None:
        self.game.press(command, when)
        self.events += self.game.pop_events()

    def test_five_commands_fixed_speed(self) -> None:
        self.assertEqual(sorted(self.game.active), ["Bop", "Flick", "Pull", "Spin", "Twist"])
        self.assertIn(ev.MusicStart("MUSIC_BlitzLoop_01a", 1.0, 1.62), self.events)
        for _ in range(15):
            now = self.next_turn()
            self.press(self.game.current or "", now + 0.2)
        self.assertEqual(self.game.pitch, 1.0)
        self.assertEqual(of(self.events, ev.SpeedUp), [])

    def test_finishes_on_twentieth_success(self) -> None:
        now = 0.0
        for _ in range(20):
            now = self.next_turn()
            self.press(self.game.current or "", now + 0.2)
        finished = of(self.events, ev.BlitzFinished)
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0].moves, 20)
        self.assertAlmostEqual(finished[0].time, now + 0.2 - 10.0)
        self.assertEqual(self.game.state, State.OVER)
        # The already queued callout is cut off and nothing else is scheduled.
        self.assertEqual(len(of(self.events, ev.StopSound)), 1)
        self.assertEqual(self.game._timers, [])

    def test_mistake_costs_time_but_game_goes_on(self) -> None:
        now = self.next_turn()
        wrong = next(c for c in self.game.active if c != self.game.current)
        self.press(wrong, now + 0.2)
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertEqual(of(self.events, ev.HelpNeeded), [])
        self.assertEqual(of(self.events, ev.GameOver), [])
        self.assertNotIn(ev.MusicStop(), self.events)
        self.assertTrue(any(p.name.startswith("VO_Die_") for p in of(self.events, ev.PlaySound)))
        # A new command is called straight away and the next turn opens a beat later.
        self.assertAlmostEqual(self.game._timers[0][0], now + 0.2 + 0.81)

    def test_timeout_also_continues(self) -> None:
        now = self.next_turn()
        self.game.update(now + 1.1)
        self.events += self.game.pop_events()
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertEqual(self.game.moves, 0)

    def test_stopwatch(self) -> None:
        self.assertAlmostEqual(self.game.blitz_elapsed(13.5), 3.5)


if __name__ == "__main__":
    unittest.main()
