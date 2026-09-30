"""The only module that talks to Prism. See docs/SPEECH_POLICY.md."""

import logging
import time
from collections.abc import Callable
from typing import Protocol

log = logging.getLogger(__name__)

# Padding added to a protected utterance's estimated length, for backend startup latency.
PROTECT_MARGIN_SECONDS = 0.3


class SpeechBackend(Protocol):
    name: str

    def speak(self, text: str, interrupt: bool) -> None: ...

    def stop(self) -> None: ...

    def is_speaking(self) -> bool | None:
        """True or False, or None when the backend cannot tell."""
        ...


class PrismBackend:
    """Adapter over a prism.Backend. Uses output() so braille displays get the text too."""

    def __init__(self, backend: object, context: object) -> None:
        # The backend is only valid while its context is alive, so hold both.
        self._context = context
        self._backend = backend
        features = backend.features
        self.name: str = backend.name
        self._use_output: bool = features.supports_output
        self._can_query: bool = features.supports_is_speaking
        self._can_stop: bool = features.supports_stop

    def speak(self, text: str, interrupt: bool) -> None:
        if self._use_output:
            self._backend.output(text, interrupt)
        else:
            self._backend.speak(text, interrupt)

    def stop(self) -> None:
        if self._can_stop:
            self._backend.stop()

    def is_speaking(self) -> bool | None:
        return bool(self._backend.speaking) if self._can_query else None


class ConsoleBackend:
    """Fallback when Prism is unavailable, so failures are never silent."""

    name = "console"

    def speak(self, text: str, interrupt: bool) -> None:
        print(f"SPEECH: {text}", flush=True)

    def stop(self) -> None:
        pass

    def is_speaking(self) -> bool | None:
        return None


class Speech:
    def __init__(
        self,
        backend: SpeechBackend,
        chars_per_second: float = 18.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.backend = backend
        self.chars_per_second = chars_per_second
        self._clock = clock
        self._protected_until: float = 0.0

    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None:
        """Speak without blocking.

        interrupt cuts off current speech, unless protected speech is still playing,
        in which case this is queued behind it. protect shields this utterance from
        later interrupts until its estimated end.
        """
        text = text.replace("\x00", "").strip()
        if not text:
            log.warning("Ignoring empty speech request")
            return
        now = self._clock()
        if interrupt and not protect and self.is_protected():
            log.debug("Protected speech active, queueing instead of interrupting: %s", text)
            interrupt = False
        if protect:
            start = now if interrupt else max(now, self._protected_until)
            self._protected_until = start + self._estimate_seconds(text)
        log.debug("speak interrupt=%s protect=%s: %s", interrupt, protect, text)
        try:
            self.backend.speak(text, interrupt)
        except Exception:
            log.exception("Speech backend %s failed to speak", self.backend.name)
            print(f"SPEECH FAILED: {text}", flush=True)

    def stop(self, force: bool = False) -> None:
        """Silence speech. Protected speech is only stopped when force is set."""
        if self.is_protected() and not force:
            log.debug("Ignoring stop while protected speech is active")
            return
        self._protected_until = 0.0
        try:
            self.backend.stop()
        except Exception:
            log.exception("Speech backend %s failed to stop", self.backend.name)

    def is_speaking(self) -> bool | None:
        """Whether speech is playing. None when the backend cannot tell, as with NVDA."""
        try:
            return self.backend.is_speaking()
        except Exception:
            log.exception("Speech backend %s failed to report speaking state", self.backend.name)
            return None

    def is_protected(self) -> bool:
        return self._clock() < self._protected_until

    def _estimate_seconds(self, text: str) -> float:
        return len(text) / self.chars_per_second + PROTECT_MARGIN_SECONDS


def create_speech(chars_per_second: float = 18.0) -> Speech:
    """Connect to the best Prism backend, falling back loudly to console output."""
    try:
        import prism

        prism.install_logging()
        context = prism.Context()
        raw = context.acquire_best()
        backend: SpeechBackend = PrismBackend(raw, context)
        log.info("Speech backend: %s (speaking state %s)", backend.name,
                 "available" if raw.features.supports_is_speaking else "not available")
    except Exception:
        log.exception("PRISM FAILED TO INITIALIZE. Speech output will go to the console only.")
        print("ERROR: Prism speech failed to initialize. Speech goes to the console only.", flush=True)
        backend = ConsoleBackend()
    return Speech(backend, chars_per_second)
