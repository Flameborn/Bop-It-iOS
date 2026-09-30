import random
import unittest

from bopit.engine import events as ev
from bopit.engine.game import Game, ModeRules, Options, State

SHOUT_ONLY = ModeRules("Test", (("Shout", 0),), pitch_shift_amount=0.0)


def of(events: list[ev.Event], kind: type) -> list:
    return [e for e in events if isinstance(e, kind)]


class ShoutMicrophoneTests(unittest.TestCase):
    def start(self, microphone: bool = True) -> float:
        self.game = Game(SHOUT_ONLY, Options(microphone=microphone), random.Random(1))
        self.game.prepare(0.0)
        self.game.press("Bop", 0.0)
        opened = self.game._timers[0][0]
        self.game.update(opened)
        self.events = self.game.pop_events()
        self.assertEqual(self.game.current, "Shout")
        return opened

    def test_listens_after_callout_length(self) -> None:
        opened = self.start()
        self.game.hear(1.0, opened + 0.3)
        self.assertEqual(self.game.state, State.IN_TURN)
        self.game.update(opened + 0.46)
        self.assertEqual(of(self.game.pop_events(), ev.MicListen), [ev.MicListen(True)])

    def test_loud_enough_wins_as_x_move(self) -> None:
        opened = self.start()
        self.game.hear(0.59, opened + 0.5)
        self.assertEqual(self.game.state, State.IN_TURN)
        self.game.hear(0.6, opened + 0.6)
        events = self.game.pop_events()
        self.assertIn(ev.XMove("Shout"), events)
        self.assertIn(ev.MicListen(False), events)
        self.assertEqual((self.game.moves, self.game.x_moves, self.game.end_bonus), (1, 1, 25))

    def test_key_still_works_and_closes_microphone(self) -> None:
        opened = self.start()
        self.game.update(opened + 0.5)
        self.game.press("Shout", opened + 0.6)
        events = self.game.pop_events()
        self.assertIn(ev.MicListen(False), events)
        self.assertEqual((self.game.moves, self.game.x_moves), (1, 0))

    def test_setting_off_never_listens(self) -> None:
        opened = self.start(microphone=False)
        self.game.update(opened + 0.9)
        self.game.hear(1.0, opened + 0.9)
        self.assertEqual(of(self.game.pop_events(), ev.MicListen), [])
        self.assertEqual(self.game.state, State.IN_TURN)


if __name__ == "__main__":
    unittest.main()
