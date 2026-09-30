import random
import unittest

from bopit.engine import events as ev
from bopit.engine.commands import all_commands, callout_sound, response_sound
from bopit.engine.game import CLASSIC, Game, Options, State


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class CommandTests(unittest.TestCase):
    def test_master_order_and_shout_setting(self) -> None:
        self.assertEqual(all_commands(True)[:6], ("Bop", "Twist", "Pull", "Spin", "Flick", "Shout"))
        self.assertNotIn("Shout", all_commands(False))
        self.assertEqual(len(all_commands(True)), 12)

    def test_sound_names(self) -> None:
        self.assertEqual(callout_sound("Bop", "VOX", 0), "VO_Bop")
        self.assertEqual(callout_sound("Bop", "SFX", 0), "SFX_Bop_C")
        self.assertEqual(response_sound("Twist", 0), "SFX_Twist_R")
        self.assertEqual(callout_sound("Crank", "SFX", 0), "SFX_Turn_C")
        self.assertEqual(response_sound("Brush", 0), "SFX_Pet_R")
        self.assertEqual(response_sound("Shout", 1), "SFX_Shout_R_HLWN")
        self.assertEqual(response_sound("Bop", 1), "SFX_Bop_R")


class ClassicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(CLASSIC, Options(), random.Random(1))
        self.game.prepare(0.0)
        self.events: list[ev.Event] = self.game.pop_events()

    def run_until(self, when: float) -> None:
        self.game.update(when)
        self.events += self.game.pop_events()

    def press(self, command: str, when: float) -> None:
        self.game.press(command, when)
        self.events += self.game.pop_events()

    def start(self, when: float = 0.0) -> None:
        self.press("Twist", when)  # Any input starts the game.

    def open_turn(self) -> float:
        """Advance to the next turn opening and return its time."""
        self.events.clear()
        now = self.game._timers[0][0]
        self.run_until(now)
        self.assertEqual(self.game.state, State.IN_TURN)
        return now

    def win_moves(self, count: int) -> float:
        now = 0.0
        for _ in range(count):
            now = self.open_turn()
            self.press(self.game.current or "", now + 0.1)
        return now + 0.1

    def test_waits_for_any_input_to_start(self) -> None:
        self.assertEqual(of(self.events, ev.WaitingToStart), [ev.WaitingToStart()])
        self.start()
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertEqual(of(self.events, ev.GameStarted), [ev.GameStarted("Classic")])

    def test_start_plays_music_and_first_callout(self) -> None:
        self.start()
        self.assertEqual(of(self.events, ev.MusicStart), [ev.MusicStart("MUSIC_GameLoop_01a", 1.0, 1.62)])
        called = of(self.events, ev.CommandCalled)[0].command
        self.assertIn(called, ("Bop", "Twist", "Pull"))
        self.assertIn(ev.PlaySound(f"VO_{called}", 1.0), self.events)

    def test_turn_opens_one_beat_after_callout(self) -> None:
        self.start(10.0)
        self.run_until(10.8)
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.run_until(10.81)
        opened = of(self.events, ev.TurnOpened)[0]
        self.assertAlmostEqual(opened.deadline, 10.81 + 1.1)

    def test_input_between_turns_is_ignored(self) -> None:
        self.start()
        self.press("Bop", 0.5)
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertEqual(of(self.events, ev.MoveMade), [])

    def test_correct_move_scores(self) -> None:
        self.start()
        now = self.open_turn()
        command = self.game.current or ""
        self.press(command, now + 0.3)
        self.assertEqual(of(self.events, ev.ScoreChanged), [ev.ScoreChanged(1, 100)])
        self.assertIn(ev.PlaySound(f"SFX_{command}_R", 1.0), self.events)
        self.assertIn(ev.MusicSegment("MUSIC_GameLoop_01b", 1.0), self.events)
        self.assertIn(ev.MusicSeek(1.62), self.events)
        self.assertEqual(len(of(self.events, ev.CommandCalled)), 1)
        # The next turn opens one beat after the success.
        self.assertAlmostEqual(self.game._timers[0][0], now + 0.3 + 0.81)

    def test_wrong_move_fails(self) -> None:
        self.start()
        now = self.open_turn()
        wrong = next(c for c in ("Bop", "Twist", "Pull") if c != self.game.current)
        self.press(wrong, now + 0.2)
        self.assertIn(self.game.state, (State.HELP, State.FAILING))
        self.assertIn(ev.MusicStop(), self.events)
        self.assertFalse(of(self.events, ev.MoveMade)[0].correct)

    def test_timeout_fails(self) -> None:
        self.start()
        now = self.open_turn()
        self.run_until(now + 1.09)
        self.assertEqual(self.game.state, State.IN_TURN)
        self.run_until(now + 1.1)
        self.assertEqual(len(of(self.events, ev.TurnTimedOut)), 1)

    def test_early_fail_shows_help_and_waits(self) -> None:
        self.start()
        now = self.open_turn()
        self.run_until(now + 1.1)
        help_event = of(self.events, ev.HelpNeeded)
        self.assertEqual(len(help_event), 1)
        self.run_until(now + 60)
        self.assertEqual(self.game.state, State.HELP)
        self.events.clear()
        self.game.dismiss_help(now + 61)
        self.events += self.game.pop_events()
        self.assertTrue(of(self.events, ev.PlaySound)[0].name.startswith("VO_Banter_"))
        self.run_until(now + 62)
        self.assertEqual(of(self.events, ev.GameOver), [ev.GameOver(0, 0, 0, 0)])

    def test_later_fail_skips_help_with_one_second_steps(self) -> None:
        self.start()
        self.win_moves(20)
        now = self.open_turn()
        self.assertGreater(self.game.times_called[self.game.current or ""], 2)
        self.run_until(now + 1.1 / self.game.pitch)
        fail_time = now + 1.1 / self.game.pitch
        self.assertEqual(of(self.events, ev.HelpNeeded), [])
        self.assertTrue(any(p.name.startswith("VO_Die_") for p in of(self.events, ev.PlaySound)))
        self.run_until(fail_time + 0.99)
        self.assertEqual(self.game.state, State.FAILING)
        self.run_until(fail_time + 2.0)
        over = of(self.events, ev.GameOver)[0]
        self.assertEqual((over.moves, over.end_bonus), (20, 0))
        self.assertEqual(over.total, over.moves + over.bonus)

    def test_banter_off(self) -> None:
        self.game.options = Options(banter=False)
        self.start()
        self.win_moves(20)
        now = self.open_turn()
        self.run_until(now + 5)
        names = [p.name for p in of(self.events, ev.PlaySound)]
        self.assertFalse(any(n.startswith("VO_Banter_") for n in names))
        self.assertEqual(len(of(self.events, ev.GameOver)), 1)

    def test_speed_up_every_12_moves(self) -> None:
        self.start()
        self.win_moves(12)
        self.assertEqual(self.game.pitch, 1.0)
        self.open_turn()  # success_done for move 12 runs as the next turn opens
        self.assertAlmostEqual(self.game.pitch, 1.03)
        self.assertIn(ev.MusicPitch(self.game.pitch), self.events)
        self.assertEqual(self.game._base_bonus, 105)

    def test_timings_shrink_with_pitch(self) -> None:
        self.start()
        self.win_moves(12)
        now = self.open_turn()
        opened = of(self.events, ev.TurnOpened)[0]
        self.assertAlmostEqual(opened.deadline - now, 1.1 / 1.03)

    def test_music_track_changes_every_third_speed_up(self) -> None:
        self.start()
        self.win_moves(36)
        self.open_turn()
        self.assertIn(ev.MusicStart("MUSIC_GameLoop_02a", self.game.pitch, 0.0), self.events)

    def test_bonus_accumulates_base_bonus(self) -> None:
        self.start()
        self.win_moves(13)
        # 12 moves at 100, then 1 at 105.
        self.assertEqual(self.game.bonus, 12 * 100 + 105)

    def test_same_seed_same_game(self) -> None:
        def sequence(seed: int) -> list[str]:
            game = Game(CLASSIC, Options(), random.Random(seed))
            game.prepare(0.0)
            game.press("Bop", 0.0)
            now = 0.0
            for _ in range(10):
                now = game._timers[0][0]
                game.update(now)
                game.press(game.current or "", now + 0.1)
            return [e.command for e in game.pop_events() if isinstance(e, ev.CommandCalled)]

        self.assertEqual(sequence(7), sequence(7))


if __name__ == "__main__":
    unittest.main()
