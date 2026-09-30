"""Speech driven menus. No pygame here, so menus can be tested headless.

Every item announces its name, its position, and its state if it has one.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class Nav(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    FIRST = auto()
    LAST = auto()
    SELECT = auto()
    BACK = auto()


class Speaker(Protocol):
    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None: ...


@dataclass
class Button:
    label: str
    on_select: Callable[[], None]
    # Played on select. The original's buttons each chose their own sound, or none.
    sound: str | None = None

    def state(self) -> str | None:
        return None


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

    def describe(self, index: int | None = None) -> str:
        index = self.focus if index is None else index
        item = self.items[index]
        parts = [item.label]
        state = item.state()
        if state is not None:
            parts.append(state)
        parts.append(f"{index + 1} of {len(self.items)}")
        return ", ".join(parts)

    def enter(self, speaker: Speaker) -> None:
        speaker.speak(f"{self.title}. {self.describe()}", interrupt=True)

    def handle(self, nav: Nav, speaker: Speaker, play: Callable[[str], None]) -> None:
        item = self.items[self.focus]
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
        speaker.speak(item.state() or "", interrupt=True)

    @staticmethod
    def _play(play: Callable[[str], None], name: str | None) -> None:
        if name is not None:
            play(name)
