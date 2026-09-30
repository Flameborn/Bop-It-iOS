import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import PASS_IT_BASIC, PASS_IT_EXTREME, Game, Options, State

PICKED = ("Twist", "Pull", "Spin", "Flick")


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


def started(rules, seed: int = 3, picked=PICKED) -> Game:
    game = Game(rules, Options(picked=picked), random.Random(seed))
    game.prepare(0.0)
    game.press("Bop", 0.0)
    return game


def play_until_pass(game: Game) -> tuple[list[ev.Event], float]:
    events: list[ev.Event] = []
    while True:
        if game.state == State.IN_TURN:
            game.press(game.current or "", game._turn_opened_at + 0.1)
        else:
            now = game._timers[0][0]
            game.update(now)
        events += game.pop_events()
        if game.state == State.PASSING:
            return events, now


class PassItTests(unittest.TestCase):
    def test_bop_plus_picked_in_their_places(self) -> None:
        game = started(PASS_IT_EXTREME)
        self.assertEqual(game.active, ["Bop", "Twist", "Pull", "Spin", "Flick"])
        self.assertEqual([game.locations[c] for c in game.active], [4, 0, 3, 2, 1])

    def test_two_picks(self) -> None:
        game = started(PASS_IT_EXTREME, picked=("Nail", "Poke"))
        self.assertEqual(game.active, ["Bop", "Nail", "Poke"])

    def test_pass_after_four_to_six(self) -> None:
        for seed in range(10):
            game = started(PASS_IT_EXTREME, seed)
            events, _ = play_until_pass(game)
            self.assertIn(game.moves, (4, 5, 6))
            self.assertIn(ev.MusicSegment("VO_Pass", 1.0), events)

    def test_pass_timing_and_next_player(self) -> None:
        game = started(PASS_IT_EXTREME)
        play_until_pass(game)
        shown = game._timers[0][0]
        game.update(shown)
        game.pop_events()
        self.assertAlmostEqual(game._timers[0][0], shown + 3.25)
        game.update(shown + 3.25)
        events = game.pop_events()
        self.assertEqual(game.state, State.IN_TURN)
        self.assertEqual(len(of(events, ev.CommandCalled)), 1)
        self.assertEqual(of(events, ev.MusicStart)[0].position, 0.0)
        # The turn opens at once, so the callout skips its one-beat lead-in.
        callout = [e for e in of(events, ev.PlaySound) if e.name.startswith("VO_")][0]
        self.assertEqual(callout.position, 0.805)

    def test_pass_waits_for_the_bar_to_end(self) -> None:
        game = started(PASS_IT_EXTREME)
        events, _ = play_until_pass(game)
        # The pass begins at the passing success: callout cut, "b" part left playing,
        # VO_Pass started so "Pass!" lands on the next downbeat.
        self.assertNotIn(ev.StopSound("MUSIC_GameLoop_01b"), events)
        self.assertNotIn(ev.MusicStop(), events)
        self.assertIn(ev.MusicSegment("VO_Pass", 1.0), events)
        success = game._turn_opened_at + 0.1
        self.assertAlmostEqual(game._timers[0][0], success + 17917 / 22050)
        downbeat = game._timers[0][0]
        game.update(downbeat)
        at_downbeat = game.pop_events()
        self.assertIn(ev.MusicStop(), at_downbeat)
        self.assertIn(ev.MusicSegment("MUSIC_PassIt_01", 1.0), at_downbeat)
        self.assertAlmostEqual(game._timers[0][0], downbeat + 3.25)

    def test_cannot_pause_while_passing(self) -> None:
        game = started(PASS_IT_EXTREME)
        _, shown = play_until_pass(game)
        self.assertFalse(game.can_pause)

    def test_pass_it_never_speeds_up(self) -> None:
        game = started(PASS_IT_EXTREME)
        for _ in range(6):
            play_until_pass(game)
            shown = game._timers[0][0]
            game.update(shown)
            game.update(shown + 3.25)
        self.assertEqual(game.pitch, 1.0)

    def test_fail_ends_game(self) -> None:
        game = started(PASS_IT_EXTREME)
        now = game._timers[0][0]
        game.update(now + 1.1)
        game.dismiss_help(now + 2)
        game.update(now + 10)
        self.assertEqual(game.state, State.OVER)

    def test_basic_starts_with_bop(self) -> None:
        game = started(PASS_IT_BASIC)
        now = game._timers[0][0]
        game.update(now)
        self.assertEqual(game.current, "Bop")
        # Counted as called three times, so failing Bop gives no help pause.
        game.update(now + 1.1)
        self.assertEqual(of(game.pop_events(), ev.HelpNeeded), [])


if __name__ == "__main__":
    unittest.main()
