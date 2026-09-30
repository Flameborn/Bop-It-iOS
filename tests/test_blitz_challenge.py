import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import (BEAT, BLITZ_CHALLENGE, CALLOUT_NOW_POSITION,
                               CHALLENGE_RESTART_DELAY, Game, Options, State)


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class BlitzChallengeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = Game(BLITZ_CHALLENGE, Options(players=3), random.Random(9))
        self.game.prepare(0.0)
        self.game.press("Bop", 10.0)
        self.events: list[ev.Event] = self.game.pop_events()

    def step(self) -> float:
        now = self.game._timers[0][0]
        self.game.update(now)
        self.events += self.game.pop_events()
        return now

    def press(self, command: str, when: float) -> None:
        self.game.press(command, when)
        self.events += self.game.pop_events()

    def play_turn(self) -> float:
        """Fifteen successes, then the step a beat later that ends the turn."""
        last = 0.0
        for _ in range(15):
            now = self.game._turn_opened_at if self.game.state == State.IN_TURN else self.step()
            last = now + 0.2
            self.press(self.game.current or "", last)
        self.step()
        return last

    def test_break_after_fifteen_moves(self) -> None:
        last = self.play_turn()
        breaks = of(self.events, ev.ChallengeBreak)
        self.assertEqual(len(breaks), 1)
        self.assertEqual(breaks[0].player, 1)
        # The clock stops at successDone, a beat after the last success.
        self.assertAlmostEqual(breaks[0].time, last + BEAT - 10.0)
        self.assertEqual(self.game.state, State.BREAK)
        self.assertEqual(self.game.moves, 0)
        self.assertEqual(self.game._timers, [])
        self.assertIn(ev.MusicStop(), self.events)

    def test_last_success_cuts_off_its_callout(self) -> None:
        for _ in range(14):
            now = self.step()
            self.press(self.game.current or "", now + 0.2)
        self.events.clear()
        now = self.step()
        self.press(self.game.current or "", now + 0.2)
        self.assertEqual(len(of(self.events, ev.StopSound)), 1)

    def test_go_starts_next_player_after_delay(self) -> None:
        self.play_turn()
        self.events.clear()
        go = 100.0
        self.game.next_player(go)
        self.assertEqual(self.game._timers[0][0], go + CHALLENGE_RESTART_DELAY)
        self.step()
        self.assertEqual(self.game.state, State.IN_TURN)
        self.assertEqual(self.game.current_player, 1)
        self.assertIn(ev.MusicStart("MUSIC_BlitzLoop_01a", 1.0, 0.0), self.events)
        calls = [p for p in of(self.events, ev.PlaySound) if p.position == CALLOUT_NOW_POSITION]
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.game.blitz_elapsed(go + CHALLENGE_RESTART_DELAY + 2.0), 2.0)

    def test_mistakes_cost_time(self) -> None:
        now = self.step()
        wrong = next(c for c in self.game.active if c != self.game.current)
        self.press(wrong, now + 0.2)
        self.assertEqual(self.game.state, State.BETWEEN_TURNS)
        self.assertEqual(of(self.events, ev.GameOver), [])

    def test_results_after_last_player(self) -> None:
        for _ in range(2):
            last = self.play_turn()
            self.game.next_player(last + 5.0)
            self.step()
        self.play_turn()
        self.assertEqual(len(of(self.events, ev.ChallengeBreak)), 2)
        finished = of(self.events, ev.ChallengeFinished)
        self.assertEqual(len(finished), 1)
        self.assertEqual(len(finished[0].times), 3)
        self.assertTrue(all(t > 0 for t in finished[0].times))
        self.assertEqual(self.game.state, State.OVER)

    def test_saved_game_keeps_only_player_count(self) -> None:
        now = self.step()
        self.press(self.game.current or "", now + 0.2)
        self.game.pause(now + 0.5)
        data = self.game.save()
        self.assertEqual(data["players"], 3)
        loaded = Game(BLITZ_CHALLENGE, Options(players=2), random.Random(1))
        loaded.load(data, 50.0)
        self.assertEqual(loaded._players, 3)
        self.assertEqual(loaded.player_times, [])


class RankingTests(unittest.TestCase):
    def test_fastest_first(self) -> None:
        from bopit.game_screen import challenge_ranking
        self.assertEqual(challenge_ranking((20.5, 12.25, 30.0)),
                         [(2, 12.25), (1, 20.5), (3, 30.0)])

    def test_ties_show_the_first_player_twice(self) -> None:
        from bopit.game_screen import challenge_ranking
        self.assertEqual(challenge_ranking((14.0, 12.0, 12.0)),
                         [(2, 12.0), (2, 12.0), (1, 14.0)])


if __name__ == "__main__":
    unittest.main()
