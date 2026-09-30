"""Speech driven menus. No pygame here, so menus can be tested headless.

Every item announces its name, its position, and its state if it has one.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from bopit.i18n import tr


class Nav(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    FIRST = auto()
    LAST = auto()
    SELECT = auto()
    BACK = auto()


# The original's mode buttons (SoloGameOptions): holding for 1.2 seconds does the hold
# action; a release within 1.1 seconds is a normal press; anything between does nothing.
HOLD_AFTER = 1.2
TAP_WITHIN = 1.1


class Speaker(Protocol):
    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None: ...


@dataclass
class Button:
    label: str
    on_select: Callable[[], None]
    # Played on select. The original's buttons each chose their own sound, or none.
    sound: str | None = None
    # A button with a hold action is selected on release, not on press.
    hold: Callable[[], None] | None = None
    get_state: Callable[[], str | None] | None = None

    def state(self) -> str | None:
        return self.get_state() if self.get_state is not None else None


@dataclass
class Choice:
    """One of several named values. Select, Left and Right move between them."""

    label: str
    options: Sequence[str]
    get: Callable[[], int]
    set: Callable[[int], None]

    def state(self) -> str | None:
        return self.options[self.get()]

    def step(self, delta: int) -> None:
        self.set((self.get() + delta) % len(self.options))


@dataclass
class Slider:
    """A value from 0 to 100 in fixed steps, adjusted with Left and Right."""

    label: str
    get: Callable[[], int]
    set: Callable[[int], None]
    step_size: int = 10

    def state(self) -> str | None:
        return f"{self.get()} percent"

    def step(self, delta: int) -> None:
        self.set(max(0, min(100, self.get() + delta * self.step_size)))


Item = Button | Choice | Slider


@dataclass
class Menu:
    """Moving focus is silent, as the original was a touch screen. Choices and sliders
    play any feedback sound from their own set callbacks."""

    title: str
    items: list[Item]
    on_back: Callable[[], None] | None = None
    back_sound: str | None = None
    wrap: bool = True
    focus: int = 0
    # (item index, press time, hold already done) while a hold button is held down.
    _held: tuple[int, float, bool] | None = None

    def describe(self, index: int | None = None) -> str:
        index = self.focus if index is None else index
        item = self.items[index]
        # Labels and states are spoken in the chosen language where the original had them.
        parts = [tr(item.label)]
        state = item.state()
        if state is not None:
            parts.append(tr(state))
        parts.append(f"{index + 1} of {len(self.items)}")
        return ", ".join(parts)

    def enter(self, speaker: Speaker) -> None:
        # A title that already ends a sentence, like a question, gets no extra full stop.
        title = tr(self.title)
        separator = " " if title[-1:] in ".?!" else ". "
        speaker.speak(f"{title}{separator}{self.describe()}", interrupt=True)

    def handle(self, nav: Nav, speaker: Speaker, play: Callable[[str], None],
               now: float = 0.0) -> None:
        item = self.items[self.focus]
        if nav == Nav.SELECT and isinstance(item, Button) and item.hold is not None:
            if self._held is None:
                self._held = (self.focus, now, False)
            return
        self._held = None
        if nav in (Nav.UP, Nav.DOWN, Nav.FIRST, Nav.LAST):
            self._move(nav, speaker)
        elif nav == Nav.SELECT:
            if isinstance(item, Button):
                self._play(play, item.sound)
                item.on_select()
            elif isinstance(item, Choice):
                self._change(item, 1, speaker)
        elif nav in (Nav.LEFT, Nav.RIGHT) and isinstance(item, (Choice, Slider)):
            self._change(item, -1 if nav == Nav.LEFT else 1, speaker)
        elif nav == Nav.BACK and self.on_back is not None:
            self._play(play, self.back_sound)
            self.on_back()

    def release(self, nav: Nav, play: Callable[[str], None], now: float) -> None:
        """A key was let go. Completes a short press of a hold button."""
        if nav != Nav.SELECT or self._held is None:
            return
        index, pressed_at, held = self._held
        self._held = None
        item = self.items[index]
        if not held and now - pressed_at <= TAP_WITHIN and isinstance(item, Button):
            self._play(play, item.sound)
            item.on_select()

    def update(self, now: float) -> None:
        if self._held is None:
            return
        index, pressed_at, held = self._held
        item = self.items[index]
        if not held and now - pressed_at >= HOLD_AFTER and isinstance(item, Button) and item.hold:
            self._held = (index, pressed_at, True)
            item.hold()

    def _move(self, nav: Nav, speaker: Speaker) -> None:
        last = len(self.items) - 1
        if nav == Nav.FIRST:
            target = 0
        elif nav == Nav.LAST:
            target = last
        else:
            target = self.focus + (-1 if nav == Nav.UP else 1)
            if self.wrap:
                target %= len(self.items)
            else:
                target = max(0, min(last, target))
        self.focus = target
        speaker.speak(self.describe(), interrupt=True)

    def _change(self, item: Choice | Slider, delta: int, speaker: Speaker) -> None:
        item.step(delta)
        speaker.speak(tr(item.state() or ""), interrupt=True)

    @staticmethod
    def _play(play: Callable[[str], None], name: str | None) -> None:
        if name is not None:
            play(name)
