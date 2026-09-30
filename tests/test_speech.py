import unittest

from bopit.speech import PROTECT_MARGIN_SECONDS, Speech


class FakeBackend:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bool]] = []
        self.speaking: bool | None = None
        self.fail = False

    def speak(self, text: str, interrupt: bool) -> None:
        if self.fail:
            raise RuntimeError("boom")
        self.calls.append(("speak", text, interrupt))

    def stop(self) -> None:
        self.calls.append(("stop", "", False))

    def is_speaking(self) -> bool | None:
        return self.speaking


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class SpeechPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = FakeBackend()
        self.clock = FakeClock()
        # 10 characters per second keeps the arithmetic readable.
        self.speech = Speech(self.backend, chars_per_second=10.0, clock=self.clock)

    def test_plain_speak_queues(self) -> None:
        self.speech.speak("Play")
        self.assertEqual(self.backend.calls, [("speak", "Play", False)])

    def test_interrupt_passes_through_when_unprotected(self) -> None:
        self.speech.speak("Settings", interrupt=True)
        self.assertEqual(self.backend.calls, [("speak", "Settings", True)])

    def test_interrupt_is_queued_while_protected(self) -> None:
        self.speech.speak("Score 1234567890", interrupt=True, protect=True)
        self.speech.speak("Play again", interrupt=True)
        self.assertEqual(self.backend.calls[1], ("speak", "Play again", False))

    def test_protection_expires_after_estimate(self) -> None:
        text = "Game over."  # 10 characters, so 1 second plus margin.
        self.speech.speak(text, interrupt=True, protect=True)
        self.clock.now += 1.0 + PROTECT_MARGIN_SECONDS + 0.01
        self.assertFalse(self.speech.is_protected())
        self.speech.speak("Play again", interrupt=True)
        self.assertEqual(self.backend.calls[1], ("speak", "Play again", True))

    def test_queued_protected_speech_extends_protection(self) -> None:
        self.speech.speak("Game over.", interrupt=True, protect=True)
        self.speech.speak("Score 42.", protect=True)
        first_end = 1.0 + PROTECT_MARGIN_SECONDS
        self.clock.now += first_end + 0.5
        self.assertTrue(self.speech.is_protected())

    def test_protected_can_interrupt_protected(self) -> None:
        self.speech.speak("Game over.", interrupt=True, protect=True)
        self.speech.speak("New high score", interrupt=True, protect=True)
        self.assertEqual(self.backend.calls[1], ("speak", "New high score", True))

    def test_stop_ignored_while_protected_unless_forced(self) -> None:
        self.speech.speak("Game over.", interrupt=True, protect=True)
        self.speech.stop()
        self.assertNotIn(("stop", "", False), self.backend.calls)
        self.speech.stop(force=True)
        self.assertIn(("stop", "", False), self.backend.calls)
        self.assertFalse(self.speech.is_protected())

    def test_empty_text_is_ignored(self) -> None:
        self.speech.speak("   ")
        self.speech.speak("\x00")
        self.assertEqual(self.backend.calls, [])

    def test_backend_failure_does_not_raise(self) -> None:
        self.backend.fail = True
        with self.assertLogs("bopit.speech", level="ERROR"):
            self.speech.speak("Bop it")

    def test_is_speaking_reports_unknown(self) -> None:
        self.assertIsNone(self.speech.is_speaking())
        self.backend.speaking = True
        self.assertTrue(self.speech.is_speaking())


if __name__ == "__main__":
    unittest.main()
