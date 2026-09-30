import argparse
import io
import random
import unittest

from bopit.debug.autoplay import LATE_BY, START_DELAY, Bot
from bopit.debug.event_log import EventLog, describe
from bopit.debug.options import DebugOptions, Failure, add_arguments, from_arguments
from bopit.engine import events as ev
from bopit.engine.game import CLASSIC, HEAD_TO_HEAD, TURN_TIMEOUT, Game, Options, State


def run(game: Game, bot: Bot, until: float) -> list[tuple[float, ev.Event]]:
    """Drive a game with the bot the way GameScreen does, without a screen."""
    seen: list[tuple[float, ev.Event]] = []

    def dispatch() -> None:
        for when, event in game.pop_timed_events():
            seen.append((when, event))
            bot.plan(when, event, game)

    game.prepare(0.0)
    dispatch()
    while game.state != State.OVER:
        pending = [t for t, _, _ in game._timers]
        action = bot._pending[0].at if bot._pending else None
        nexts = pending + ([action] if action is not None else [])
        if not nexts or min(nexts) > until:
            break
        now = min(nexts)
        game.update(now)
        dispatch()
        due = bot.due(now)
        if due is not None:
            if due.player is not None:
                game.press_by(due.player, due.command, due.at)
            else:
                game.press(due.command, due.at)
            dispatch()
    return seen


class BotTests(unittest.TestCase):
    def test_plays_perfectly_at_its_reaction_time(self) -> None:
        game = Game(CLASSIC, Options(), random.Random(1))
        seen = run(game, Bot(DebugOptions(reaction=0.25)), until=60.0)
        moves = [e for _, e in seen if isinstance(e, ev.MoveMade)]
        self.assertGreater(len(moves), 30)
        self.assertTrue(all(m.correct for m in moves))
        # 0.25 at normal speed, shrinking with the pitch as the game speeds up.
        self.assertAlmostEqual(moves[0].reaction, 0.25)
        self.assertLess(moves[-1].reaction, 0.25)
        self.assertAlmostEqual(moves[-1].reaction * game.pitch, 0.25)
        started = next(t for t, e in seen if isinstance(e, ev.GameStarted))
        self.assertEqual(started, START_DELAY)

    def test_wrong_on_every_fifth_turn_ends_classic(self) -> None:
        game = Game(CLASSIC, Options(), random.Random(1))
        seen = run(game, Bot(DebugOptions(failure=Failure.WRONG, fail_every=5)), until=60.0)
        moves = [e for _, e in seen if isinstance(e, ev.MoveMade)]
        self.assertEqual(len(moves), 5)
        self.assertFalse(moves[-1].correct)
        self.assertTrue(any(isinstance(e, ev.GameOver) for _, e in seen))

    def test_late_press_comes_after_timeout(self) -> None:
        game = Game(CLASSIC, Options(), random.Random(1))
        bot = Bot(DebugOptions(failure=Failure.LATE, fail_every=1))
        seen = run(game, bot, until=10.0)
        opened = next(t for t, e in seen if isinstance(e, ev.TurnOpened))
        timed_out = next(t for t, e in seen if isinstance(e, ev.TurnTimedOut))
        self.assertAlmostEqual(timed_out, opened + TURN_TIMEOUT)
        self.assertFalse(any(isinstance(e, ev.MoveMade) for _, e in seen))

    def test_miss_does_nothing(self) -> None:
        game = Game(CLASSIC, Options(), random.Random(1))
        seen = run(game, Bot(DebugOptions(failure=Failure.MISS, fail_every=1)), until=10.0)
        self.assertTrue(any(isinstance(e, ev.TurnTimedOut) for _, e in seen))
        self.assertFalse(any(isinstance(e, ev.MoveMade) for _, e in seen))

    def test_same_seed_same_run(self) -> None:
        def names() -> list[str]:
            game = Game(CLASSIC, Options(), random.Random(42))
            seen = run(game, Bot(DebugOptions()), until=30.0)
            return [e.command for _, e in seen if isinstance(e, ev.CommandCalled)]
        self.assertEqual(names(), names())

    def test_head_to_head_plays_as_owner(self) -> None:
        game = Game(HEAD_TO_HEAD, Options(picked=("Twist", "Pull")), random.Random(2))
        seen = run(game, Bot(DebugOptions()), until=120.0)
        self.assertTrue(any(isinstance(e, ev.HeadToHeadWon) for _, e in seen))
        wrong = [e for _, e in seen if isinstance(e, ev.MoveMade) and not e.correct]
        self.assertEqual(wrong, [])


class EventLogTests(unittest.TestCase):
    def test_lines_relative_to_first(self) -> None:
        stream = io.StringIO()
        log = EventLog(stream)
        log.line(100.0, "screen: Classic")
        log.event(101.5, ev.CommandCalled("Twist"))
        log.event(102.31, ev.TurnOpened("Twist", 103.41))
        self.assertEqual(stream.getvalue().splitlines(), [
            "0.000 screen: Classic",
            "1.500 command called: Twist",
            "2.310 turn opened: Twist, window 1.100",
        ])

    def test_every_event_type_has_a_line(self) -> None:
        samples = [ev.MoveMade("Bop", "Twist", False, 0.3), ev.ScoreChanged(3, 300),
                   ev.GameOver(3, 300, 0, 303), ev.PointScored(0, (1, 0)),
                   ev.PlaySound("VO_Bop", 1.0, 0.805, -0.8), ev.MusicStop(), ev.PassIt()]
        for event in samples:
            self.assertIsNotNone(describe(event))
        self.assertEqual(describe(ev.MoveMade("Bop", "Twist", False, 0.3)),
                         "response: Bop, expected Twist, wrong, delta 0.300")


class OptionsTests(unittest.TestCase):
    def parse(self, *argv: str) -> DebugOptions | None:
        parser = argparse.ArgumentParser()
        add_arguments(parser)
        return from_arguments(parser.parse_args(list(argv)))

    def test_off_by_default(self) -> None:
        self.assertIsNone(self.parse())

    def test_flags(self) -> None:
        options = self.parse("--debug", "--fail", "late", "--fail-every", "3", "--seed", "9",
                             "--reaction", "1.05")
        self.assertEqual(options, DebugOptions(True, 1.05, Failure.LATE, 3, 9))
        self.assertFalse(self.parse("--debug", "--no-bot").bot)


if __name__ == "__main__":
    unittest.main()
