import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import BASIC, CLASSIC, EXTREME, LOOP_LENGTHS, Game, ModeRules, Options, State
from bopit.engine.rhythm import Grade, RhythmState, Streak

LOOP = LOOP_LENGTHS["MUSIC_GameLoop_01a"]


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class Player:
    """Plays a game perfectly, pressing a set time after each turn opens."""

    def __init__(self, rules: ModeRules, delay: float = 0.1, seed: int = 3,
                 options: Options = Options()) -> None:
        self.game = Game(rules, options, random.Random(seed))
        self.delay = delay
        self.events: list[ev.Event] = []
        self.game.prepare(0.0)
        self.game.press("Bop", 0.0)
        self.events += self.game.pop_events()
        self.calls: list[str] = []

    def win(self, count: int) -> None:
        for _ in range(count):
            opened = self.game._timers[0][0]
            self.game.update(opened)
            self.calls.append(self.game.current or "")
            self.game.press(self.game.current or "", opened + self.delay / self.game.pitch)
            self.events += self.game.pop_events()


class BasicTests(unittest.TestCase):
    def test_bop_only_at_start_then_scripted_twist_and_pull(self) -> None:
        player = Player(BASIC)
        self.assertEqual(player.game.active, ["Bop"])
        player.win(8)
        # Bop, Bop, then Twist is introduced on turn 3; Pull on turn 8.
        self.assertEqual(player.calls[:3], ["Bop", "Bop", "Twist"])
        self.assertEqual(player.calls[7], "Pull")
        self.assertEqual(player.game.active, ["Bop", "Twist", "Pull"])
        self.assertEqual(player.game.locations, {"Bop": 4, "Twist": 0, "Pull": 3})

    def test_unlock_schedule(self) -> None:
        player = Player(BASIC)
        player.win(60)
        unlocks = [(i, e.command) for i, e in enumerate(player.events) if isinstance(e, ev.CommandUnlocked)]
        names = [c for _, c in unlocks]
        self.assertEqual(names[:4], ["Spin", "Flick", "Shout", "Squeeze"])
        # Unlocked on successes 15, 24, 34 and 45: gaps of 9, 10 and 11.
        # Each unlock happens during a win, after that win's score update.
        wins_at_unlock = [len(of(player.events[:i], ev.ScoreChanged)) for i, _ in unlocks]
        self.assertEqual(wins_at_unlock[:4], [15, 24, 34, 45])
        # The new command is called straight away and is the next turn.
        self.assertEqual(player.calls[15], "Spin")

    def test_positions_rotate_after_five(self) -> None:
        player = Player(BASIC)
        player.win(46)
        game = player.game
        # Spin took position 2, Flick 1, Shout replaced Twist at 0, Squeeze replaced Pull at 3.
        self.assertEqual(game.active, ["Bop", "Spin", "Flick", "Shout", "Squeeze"])
        self.assertEqual([game.locations[c] for c in game.active], [4, 2, 1, 0, 3])

    def test_introductions_are_announced(self) -> None:
        player = Player(BASIC)
        player.win(24)
        introduced = [e.command for e in of(player.events, ev.CommandIntroduced)]
        self.assertEqual(introduced, ["Twist", "Pull", "Spin", "Flick"])

    def test_poke_takes_its_own_position(self) -> None:
        game = Game(BASIC, Options(), random.Random(1))
        game.active = ["Bop", "Spin", "Flick", "Shout", "Squeeze"]
        game.locations = {"Bop": 4, "Spin": 2, "Flick": 1, "Shout": 0, "Squeeze": 3}
        game._activate("Poke", 1)
        self.assertEqual(len(game.active), 6)
        self.assertEqual(game.locations["Poke"], 5)

    def test_perfect_timing_earns_end_bonus(self) -> None:
        # The loop wraps as the turn opens, so one beat later lands in the Perfect window.
        player = Player(BASIC, delay=0.81)
        player.win(5)
        grades = [e.grade for e in of(player.events, ev.RhythmGraded)]
        self.assertEqual(grades, ["Perfect"] * 5)
        self.assertEqual(player.game.end_bonus, 5 * 75)

    def test_early_press_is_ok(self) -> None:
        player = Player(BASIC, delay=0.1)
        player.win(3)
        self.assertEqual([e.grade for e in of(player.events, ev.RhythmGraded)], ["OK"] * 3)
        self.assertEqual(player.game.end_bonus, 0)

    def test_perfect_streak_after_25(self) -> None:
        player = Player(BASIC, delay=0.81)
        player.win(25)
        self.assertEqual(of(player.events, ev.StreakEarned), [ev.StreakEarned("Perfect")])
        self.assertEqual(player.game.end_bonus, 25 * 75 + 100)

    def test_end_bonus_kept_in_total(self) -> None:
        player = Player(BASIC, delay=0.81)
        player.win(3)
        now = player.game._timers[0][0]
        player.game.update(now)
        player.game.update(now + 5)
        player.game.dismiss_help(now + 5)
        player.game.update(now + 10)
        over = of(player.game.pop_events(), ev.GameOver)[0]
        self.assertEqual(over.end_bonus, 3 * 75)
        self.assertEqual(over.total, over.moves + over.bonus + over.end_bonus)


class ExtremeTests(unittest.TestCase):
    def test_same_script_as_basic(self) -> None:
        player = Player(EXTREME)
        player.win(16)
        self.assertEqual(player.calls[:3], ["Bop", "Bop", "Twist"])
        self.assertEqual(player.calls[15], "Spin")

    def test_help_counts_differ_from_basic(self) -> None:
        basic = Player(BASIC)
        extreme = Player(EXTREME)
        basic.win(1)
        extreme.win(1)
        # Basic set Bop's call count to 1 on the first success, Extreme to 0.
        self.assertEqual(basic.game.times_called["Bop"], 1)
        self.assertEqual(extreme.game.times_called["Bop"], 0)


class ClassicStillFixedTests(unittest.TestCase):
    def test_classic_never_unlocks_or_grades(self) -> None:
        player = Player(CLASSIC, delay=0.81)
        player.win(40)
        self.assertEqual(of(player.events, ev.CommandUnlocked), [])
        self.assertEqual(of(player.events, ev.RhythmGraded), [])
        self.assertEqual(sorted(player.game.active), ["Bop", "Pull", "Twist"])


class RhythmStateTests(unittest.TestCase):
    def test_windows(self) -> None:
        cases = [(0.80, Grade.PERFECT), (0.76, Grade.GOOD), (0.86, Grade.GOOD),
                 (0.3, Grade.OK), (1.5, Grade.OK), (2.2, Grade.MISSED)]
        for position, expected in cases:
            self.assertEqual(RhythmState().grade(position), expected, position)

    def test_ok_resets_streak(self) -> None:
        state = RhythmState(streak=Streak.PERFECT)
        state.grade(0.3)
        self.assertEqual(state.streak, Streak.NONE)

    def test_bonus_by_streak(self) -> None:
        state = RhythmState(streak=Streak.GOOD)
        state.grade(0.80)
        state.grade(0.76)
        self.assertEqual(state.end_bonus, 85 + 60)


if __name__ == "__main__":
    unittest.main()
