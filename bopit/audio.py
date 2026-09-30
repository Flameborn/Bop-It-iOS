"""The only game audio path: OpenAL Soft through cyal.

All sounds are decoded into memory up front. They are uploaded to OpenAL buffers once
a device is open, and a fixed pool of sources is created so nothing is allocated mid-game.
"""

import logging
import math
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

import soundfile

from bopit.openal_loader import loaded_openal_path, preload_openal

log = logging.getLogger(__name__)

SOURCE_POOL_SIZE = 32
RECONNECT_INTERVAL_SECONDS = 2.0


@dataclass(frozen=True)
class DecodedSound:
    pcm: bytes
    sample_rate: int
    channels: int


def decode_wav(path: Path) -> DecodedSound:
    data, sample_rate = soundfile.read(path, dtype="int16", always_2d=True)
    return DecodedSound(data.tobytes(), sample_rate, data.shape[1])


class Voice:
    """A handle to one playing sound. Stale handles are harmless."""

    def __init__(self, source: object, generation: int, audio: "Audio") -> None:
        self._source = source
        self._generation = generation
        self._audio = audio
        self.started_at: float = time.perf_counter()

    def _valid(self) -> bool:
        return self._audio._generation_of(self._source) == self._generation

    def stop(self) -> None:
        if self._valid():
            self._source.stop()

    def seek(self, seconds: float) -> None:
        """Jump to a position in the sound, in seconds of the file."""
        if self._valid():
            self._source.set("sec_offset", float(seconds))

    def set_pitch(self, pitch: float) -> None:
        if self._valid():
            self._source.pitch = pitch

    @property
    def position(self) -> float:
        """Current position in seconds of the file, or 0 if no longer playing."""
        return self._source.get_float("sec_offset") if self._valid() else 0.0

    @property
    def playing(self) -> bool:
        return self._valid() and self._audio._is_playing(self._source)


class Audio:
    def __init__(self, notify: Callable[[str], None], master_volume: float = 1.0,
                 effects_volume: float = 1.0, music_volume: float = 1.0) -> None:
        """notify is called with short spoken messages about device problems. Volumes are 0 to 1."""
        self._notify = notify
        self._sounds: dict[str, DecodedSound] = {}
        self._language = "en"
        self._buffers: dict[str, object] = {}
        self._sources: list[object] = []
        self._generations: dict[int, int] = {}
        self._next_source = 0
        self._device: object | None = None
        self._context: object | None = None
        self._connected = False
        self._next_reconnect = 0.0
        self.master_volume = master_volume
        self.effects_volume = effects_volume
        self.music_volume = music_volume
        # Per source: the gain asked for at play time, and whether it is music.
        self._source_mix: dict[int, tuple[float, bool]] = {}

    # Loading

    def load_directory(self, directory: Path, pattern: str = "*.wav",
                       skip: tuple[str, ...] = ()) -> int:
        """Decode every matching file in the tree, keyed by file stem so folders can change
        freely. Top level folders named in skip are left out."""
        paths = sorted(p for p in directory.rglob(pattern)
                       if p.relative_to(directory).parts[0] not in skip)
        seen: dict[str, Path] = {}
        for path in paths:
            if path.stem in seen:
                log.error("Duplicate sound name %s: %s and %s", path.stem, seen[path.stem], path)
            seen[path.stem] = path
        self.load_files(paths)
        return len(seen)

    def load_files(self, paths: Iterable[Path]) -> None:
        for path in paths:
            try:
                self._sounds[path.stem] = decode_wav(path)
            except Exception:
                log.exception("Could not decode %s", path)
        if self._connected:
            self._upload_buffers()

    def load_language(self, code: str, directory: Path) -> int:
        """Decode one language's recordings. They play in place of the sounds with the same
        names while that language is chosen."""
        paths = sorted(directory.glob("*.wav"))
        for path in paths:
            try:
                self._sounds[f"{code}/{path.stem}"] = decode_wav(path)
            except Exception:
                log.exception("Could not decode %s", path)
        if self._connected:
            self._upload_buffers()
        return len(paths)

    def set_language(self, code: str) -> None:
        """Play this language's recordings where it has them. As with the original's
        localized folders, anything a language does not have (like the Halloween and
        Christmas death lines) is the shared sound."""
        self._language = code

    def _localized(self, name: str) -> str:
        if self._language != "en":
            key = f"{self._language}/{name}"
            if key in self._sounds:
                return key
        return name

    @property
    def sound_names(self) -> list[str]:
        return sorted(self._sounds)

    # Device

    def open(self) -> bool:
        """Open the default device. Returns False, after telling the player, if there is none."""
        preload_openal()
        import cyal

        try:
            self._device = cyal.Device()
            self._context = cyal.Context(self._device, make_current=True)
        except Exception:
            log.exception("No audio device could be opened")
            self._notify("No audio device found. Playing without sound.")
            self._device = None
            self._context = None
            self._next_reconnect = time.monotonic() + RECONNECT_INTERVAL_SECONDS
            return False
        self._connected = True
        self._sources = list(self._context.gen_sources(SOURCE_POOL_SIZE))
        self._generations = {id(s): 0 for s in self._sources}
        self._upload_buffers()
        self._apply_master_volume()
        log.info("Audio device open: %s, library %s", self._device.name, loaded_openal_path())
        return True

    def update(self) -> None:
        """Call once per frame. Detects lost devices and reconnects."""
        if self._context is None:
            if time.monotonic() >= self._next_reconnect:
                self._next_reconnect = time.monotonic() + RECONNECT_INTERVAL_SECONDS
                if self._try_open_quietly():
                    self._notify("Audio device connected.")
            return
        connected = self._context.is_connected
        if connected and self._connected:
            return
        if self._connected:
            log.error("Audio device disconnected")
            self._notify("Audio device lost.")
            self._connected = False
            self._next_reconnect = 0.0
        if time.monotonic() >= self._next_reconnect:
            self._next_reconnect = time.monotonic() + RECONNECT_INTERVAL_SECONDS
            try:
                # Rebinds to the current default output. Buffers and sources survive.
                self._device.reopen()
            except Exception:
                log.debug("Audio device reopen failed, will retry", exc_info=True)
                return
            if self._context.is_connected:
                self._connected = True
                log.info("Audio device reconnected: %s", self._device.name)
                self._notify("Audio device restored.")

    def _try_open_quietly(self) -> bool:
        # Retries happen every couple of seconds, so do not repeat the "no device" message.
        notify, self._notify = self._notify, lambda _message: None
        try:
            return self.open()
        finally:
            self._notify = notify

    def close(self) -> None:
        for source in self._sources:
            source.stop()
        self._sources.clear()
        self._buffers.clear()
        self._context = None
        self._device = None
        self._connected = False

    def _upload_buffers(self) -> None:
        import cyal

        formats = {1: cyal.BufferFormat.MONO16, 2: cyal.BufferFormat.STEREO16}
        for name, sound in self._sounds.items():
            if name in self._buffers:
                continue
            buffer = self._context.gen_buffer()
            buffer.set_data(sound.pcm, sample_rate=sound.sample_rate, format=formats[sound.channels])
            self._buffers[name] = buffer

    # Playback

    def play(self, name: str, *, gain: float = 1.0, pitch: float = 1.0, pan: float = 0.0,
             loop: bool = False, music: bool = False) -> Voice | None:
        """Play a loaded sound now. pan runs from -1 (left) to 1 (right), mono sounds only.

        music selects the music volume instead of the effects volume.

        Returns None when the sound is unknown or there is no device.
        """
        name = self._localized(name)
        if name not in self._sounds:
            log.error("Unknown sound: %s", name)
            return None
        if not self._connected:
            log.debug("No audio device, skipping sound %s", name)
            return None
        source = self._claim_source()
        source.buffer = self._buffers[name]
        self._source_mix[id(source)] = (gain, music)
        source.gain = self._mixed_gain(gain, music)
        source.pitch = pitch
        source.looping = loop
        source.relative = True
        # A point on the unit circle in front of the listener, so distance stays constant.
        angle = max(-1.0, min(1.0, pan)) * math.pi / 2
        source.position = (math.sin(angle), 0.0, -math.cos(angle))
        source.play()
        voice = Voice(source, self._generations[id(source)], self)
        log.debug("play %s gain=%.2f pitch=%.2f pan=%.2f loop=%s music=%s",
                  name, gain, pitch, pan, loop, music)
        return voice

    def stop_all(self) -> None:
        for source in self._sources:
            source.stop()

    def duration(self, name: str) -> float:
        sound = self._sounds[name]
        return len(sound.pcm) / (2 * sound.channels * sound.sample_rate)

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = max(0.0, min(1.0, volume))
        self._apply_master_volume()

    def set_mix(self, effects_volume: float, music_volume: float) -> None:
        """Change effects and music volume, including sounds already playing."""
        self.effects_volume = max(0.0, min(1.0, effects_volume))
        self.music_volume = max(0.0, min(1.0, music_volume))
        for source in self._sources:
            mix = self._source_mix.get(id(source))
            if mix is not None:
                source.gain = self._mixed_gain(*mix)

    def _mixed_gain(self, gain: float, music: bool) -> float:
        return max(0.0, gain * (self.music_volume if music else self.effects_volume))

    def _apply_master_volume(self) -> None:
        if self._context is not None:
            self._context.listener.gain = self.master_volume

    def _claim_source(self) -> object:
        """Pick an idle source in rotation, or steal the next one if all are busy."""
        import cyal

        count = len(self._sources)
        for offset in range(count):
            index = (self._next_source + offset) % count
            source = self._sources[index]
            # Paused sources are still in use, for example music under a pause menu.
            if source.state in (cyal.SourceState.INITIAL, cyal.SourceState.STOPPED):
                break
        else:
            index = self._next_source
            source = self._sources[index]
            log.warning("All %d audio sources busy, stealing one", count)
        self._next_source = (index + 1) % count
        source.stop()
        self._generations[id(source)] += 1
        return source

    def _generation_of(self, source: object) -> int:
        return self._generations.get(id(source), -1)

    def _is_playing(self, source: object) -> bool:
        import cyal

        return source.state == cyal.SourceState.PLAYING
