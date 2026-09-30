import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import (BEAT, BLUE, GREEN, HEAD_TO_HEAD, LOOP_OFFSET, Game, Options,
                               State)

PICKED = ("Twist", "Pull", "Spin", "Flick")


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class HeadToHeadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(HEAD_TO_HEAD, Options(picked=PICKED), random.Random(3))
        self.game.prepare(0.0)
        self.game.press_by(GREEN, "Bop", 10.0)
        self.events: list[ev.Event] = self.game.pop_events()

    def open_turn(self, command: str | None = None) -> float:
        """Run to the next open turn, forcing its command if asked."""
        while self.game.state != State.IN_TURN:
            now = self.game._timers[0][0]
            self.game.update(now)
        if command is not None:
            self.game.current = command
        self.events += self.game.pop_events()
        return self.game._turn_opened_at

    def press(self, player: int, command: str, when: float) -> None:
        self.game.press_by(player, command, when)
        self.events += self.game.pop_events()

    def test_ownership_follows_picks(self) -> None:
        self.assertEqual(self.game.commands_of(GREEN), ["Pull", "Spin"])
        self.assertEqual(self.game.commands_of(BLUE), ["Twist", "Flick"])
        self.assertIsNone(self.game.owner("Bop"))

    def test_own_command_scores_nothing(self) -> None:
        now = self.open_turn("Pull")
        self.press(GREEN, "Pull", now + 0.2)
        self.assertEqual(self.game.h2h_scores, [0, 0])
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)

    def test_first_bop_scores(self) -> None:
        now = self.open_turn("Bop")
        self.press(BLUE, "Bop", now + 0.2)
        self.press(GREEN, "Bop", now + 0.25)
        self.assertEqual(self.game.h2h_scores, [0, 1])
        self.assertEqual(of(self.events, ev.PointScored), [ev.PointScored(BLUE, (0, 1))])

    def test_wrong_own_command_gives_opponent_point(self) -> None:
        now = self.open_turn("Pull")
        self.press(GREEN, "Spin", now + 0.2)
        self.assertEqual(self.game.h2h_scores, [0, 1])

    def test_pressing_on_opponents_command_gives_them_point(self) -> None:
        now = self.open_turn("Twist")
        self.press(GREEN, "Bop", now + 0.2)
        self.assertEqual(self.game.h2h_scores, [0, 1])

    def test_timeout_blames_owner_and_bop_timeout_nobody(self) -> None:
        self.open_turn("Twist")
        self.game.update(self.game._timers[0][0])
        self.assertEqual(self.game.h2h_scores, [1, 0])
        self.open_turn("Bop")
        self.game.update(self.game._timers[0][0])
        self.assertEqual(self.game.h2h_scores, [1, 0])

    def test_fail_restarts_music_and_calls_next(self) -> None:
        now = self.open_turn("Pull")
        self.events.clear()
        self.press(GREEN, "Spin", now + 0.2)
        self.assertIn(ev.MusicStop(), self.events)
        self.assertEqual(of(self.events, ev.MusicStart)[0].position, LOOP_OFFSET)
        self.assertEqual(len(of(self.events, ev.CommandCalled)), 1)
        self.assertEqual(self.game._timers[0][0], now + 0.2 + BEAT)
        self.assertEqual(of(self.events, ev.GameOver), [])

    def test_seven_wins(self) -> None:
        for _ in range(7):
            now = self.open_turn("Bop")
            self.press(GREEN, "Bop", now + 0.1)
        won = of(self.events, ev.HeadToHeadWon)
        self.assertEqual(won, [ev.HeadToHeadWon(GREEN, (7, 0), (1, 0))])
        self.assertEqual(self.game.state, State.OVER)
        self.assertEqual(self.game._timers, [])

    def test_callouts_panned_by_owner(self) -> None:
        self.events.clear()
        self.game._call("Twist")
        self.game._call("Pull")
        self.game._call("Bop")
        pans = [p.pan for p in of(self.game.pop_events(), ev.PlaySound)
                if p.name not in ("green", "blue")]
        self.assertEqual(len(pans), 3)
        self.assertGreater(pans[0], 0)
        self.assertLess(pans[1], 0)
        self.assertEqual(pans[2], 0.0)

    def test_side_cue_with_the_voice_only_when_side_changes(self) -> None:
        self.game.pop_events()
        self.game._last_side = None
        cues = []
        for command in ("Pull", "Bop", "Spin", "Twist", "Flick", "Pull"):
            self.game._call(command)
            # Nothing yet: the callout is still in its silent lead-in.
            called = [p.name for p in of(self.game.pop_events(), ev.PlaySound)]
            self.assertNotIn("green", called)
            self.assertNotIn("blue", called)
            self.game._next = command
            self.game._start_turn(0.0)
            self.game._timers.clear()
            cues += [(p.name, p.pan) for p in of(self.game.pop_events(), ev.PlaySound)]
        self.assertEqual(cues, [("green", -0.8), ("blue", 0.8), ("green", -0.8)])

    def test_speeds_up_every_eight_moves(self) -> None:
        for _ in range(8):
            now = self.open_turn("Pull")
            self.press(GREEN, "Pull", now + 0.1)
        self.game.update(self.game._timers[0][0])
        self.assertAlmostEqual(self.game.pitch, 1.02)


if __name__ == "__main__":
    unittest.main()
