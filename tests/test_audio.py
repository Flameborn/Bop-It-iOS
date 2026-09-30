import tempfile
import unittest
from pathlib import Path

import numpy
import soundfile

from bopit.audio import Audio, decode_wav


class AudioLoadingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        # Half a second of stereo silence at 22050 Hz, like many of the original files.
        soundfile.write(self.dir / "SFX_Test.wav", numpy.zeros((11025, 2), dtype="int16"), 22050)
        self.messages: list[str] = []
        self.audio = Audio(self.messages.append)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_decode_keeps_format(self) -> None:
        sound = decode_wav(self.dir / "SFX_Test.wav")
        self.assertEqual((sound.sample_rate, sound.channels, len(sound.pcm)), (22050, 2, 11025 * 4))

    def test_load_directory_keys_by_stem(self) -> None:
        self.assertEqual(self.audio.load_directory(self.dir), 1)
        self.assertEqual(self.audio.sound_names, ["SFX_Test"])
        self.assertAlmostEqual(self.audio.duration("SFX_Test"), 0.5)

    def test_load_directory_searches_subfolders(self) -> None:
        nested = self.dir / "commands" / "voice"
        nested.mkdir(parents=True)
        soundfile.write(nested / "VO_Test.wav", numpy.zeros(100, dtype="int16"), 22050)
        self.assertEqual(self.audio.load_directory(self.dir), 2)
        self.assertEqual(self.audio.sound_names, ["SFX_Test", "VO_Test"])

    def test_duplicate_names_are_reported(self) -> None:
        (self.dir / "other").mkdir()
        soundfile.write(self.dir / "other" / "SFX_Test.wav", numpy.zeros(100, dtype="int16"), 22050)
        with self.assertLogs("bopit.audio", level="ERROR"):
            self.assertEqual(self.audio.load_directory(self.dir), 1)

    def test_play_without_device_is_silent_and_safe(self) -> None:
        self.audio.load_directory(self.dir)
        self.assertIsNone(self.audio.play("SFX_Test"))
        with self.assertLogs("bopit.audio", level="ERROR"):
            self.assertIsNone(self.audio.play("missing"))


if __name__ == "__main__":
    unittest.main()
