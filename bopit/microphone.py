"""Microphone level for the Shout It X-Move, through OpenAL Soft capture.

Only the input level is measured. Captured audio is never played back.
"""

import array
import logging
import math

from bopit.openal_loader import preload_openal

log = logging.getLogger(__name__)

SAMPLE_RATE = 44100
# The original's meter (AudioQueue, linear) averaged over its small capture buffers,
# about 8 milliseconds each. Measure the same span of the newest input.
METER_FRAMES = 367
CAPTURE_BUFFER_FRAMES = SAMPLE_RATE // 2


class Microphone:
    def __init__(self) -> None:
        self._device: object | None = None
        self._capturing = False
        self._level = 0.0

    def open(self) -> bool:
        """Open the default input device. Returns False if there is none."""
        if self._device is not None:
            return True
        preload_openal()
        import cyal

        try:
            capture = cyal.CaptureExtension()
            self._device = capture.open_device(format=cyal.BufferFormat.MONO16,
                                               sample_rate=SAMPLE_RATE,
                                               buf_size=CAPTURE_BUFFER_FRAMES)
        except Exception:
            log.exception("No microphone could be opened")
            self._device = None
            return False
        log.info("Microphone open: %s", self._device.name)
        return True

    def start(self) -> None:
        if self._device is None or self._capturing:
            return
        self._drain()
        self._device.start()
        self._capturing = True
        self._level = 0.0

    def stop(self) -> None:
        if self._device is None or not self._capturing:
            return
        self._device.stop()
        self._drain()
        self._capturing = False
        self._level = 0.0

    def level(self) -> float:
        """Average power, 0 to 1, of the newest input. Keeps the last value between reads."""
        if self._device is None or not self._capturing:
            return 0.0
        samples = self._drain()
        if len(samples) >= METER_FRAMES:
            recent = samples[-METER_FRAMES:]
            self._level = math.sqrt(sum(s * s for s in recent) / len(recent)) / 32768
        return self._level

    def close(self) -> None:
        self.stop()
        self._device = None

    def _drain(self) -> array.array:
        """Read and return everything captured so far."""
        samples = array.array("h")
        if self._device is None:
            return samples
        available = self._device.available_samples
        if available > 0:
            raw = bytearray(available * 2)
            self._device.capture_samples(raw)
            samples.frombytes(bytes(raw))
        return samples
