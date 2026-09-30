import unittest

from bopit.menu import Button, Choice, Menu, Nav, Slider


class RecordingSpeaker:
    def __init__(self) -> None:
        self.spoken: list[tuple[str, bool]] = []

    def speak(self, text: str, interrupt: bool = False, protect: bool = False) -> None:
        self.spoken.append((text, interrupt))

    @property
    def last(self) -> str:
        return self.spoken[-1][0]


class MenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.speaker = RecordingSpeaker()
        self.played: list[str] = []
        self.selected: list[str] = []
        self.commands = 0
        self.music = 50
        self.backed = False

        def set_commands(value: int) -> None:
            self.commands = value

        def set_music(value: int) -> None:
            self.music = value

        def go_back() -> None:
            self.backed = True

        self.menu = Menu(
            "Settings",
            [
                Button("Play", lambda: self.selected.append("Play"), "SFX_Select"),
                Choice("Commands", ["VOX", "SFX", "Silent"], lambda: self.commands, set_commands),
                Slider("Music", lambda: self.music, set_music),
            ],
            on_back=go_back,
            back_sound="SFX_Back",
        )

    def nav(self, *moves: Nav) -> None:
        for move in moves:
            self.menu.handle(move, self.speaker, self.played.append)

    def test_enter_announces_title_and_focused_item(self) -> None:
        self.menu.enter(self.speaker)
        self.assertEqual(self.speaker.spoken, [("Settings. Play, 1 of 3", True)])

    def test_items_announce_state_and_position(self) -> None:
        self.nav(Nav.DOWN)
        self.assertEqual(self.speaker.last, "Commands, VOX, 2 of 3")
        self.nav(Nav.DOWN)
        self.assertEqual(self.speaker.last, "Music, 50 percent, 3 of 3")

    def test_navigation_interrupts(self) -> None:
        self.nav(Nav.DOWN, Nav.DOWN)
        self.assertTrue(all(interrupt for _, interrupt in self.speaker.spoken))

    def test_wraps_by_default(self) -> None:
        self.nav(Nav.UP)
        self.assertEqual(self.speaker.last, "Music, 50 percent, 3 of 3")

    def test_no_wrap_stops_at_edges(self) -> None:
        self.menu.wrap = False
        self.nav(Nav.UP)
        self.assertEqual(self.speaker.last, "Play, 1 of 3")

    def test_first_and_last(self) -> None:
        self.nav(Nav.LAST)
        self.assertEqual(self.menu.focus, 2)
        self.nav(Nav.FIRST)
        self.assertEqual(self.menu.focus, 0)

    def test_select_button_plays_sound_then_acts(self) -> None:
        self.nav(Nav.SELECT)
        self.assertEqual(self.selected, ["Play"])
        self.assertEqual(self.played, ["SFX_Select"])

    def test_choice_cycles_and_announces(self) -> None:
        self.nav(Nav.DOWN, Nav.SELECT)
        self.assertEqual((self.commands, self.speaker.last), (1, "SFX"))
        self.nav(Nav.LEFT, Nav.LEFT)
        self.assertEqual((self.commands, self.speaker.last), (2, "Silent"))

    def test_slider_steps_and_clamps(self) -> None:
        self.nav(Nav.LAST, Nav.RIGHT)
        self.assertEqual((self.music, self.speaker.last), (60, "60 percent"))
        for _ in range(10):
            self.nav(Nav.RIGHT)
        self.assertEqual(self.music, 100)

    def test_moving_focus_is_silent(self) -> None:
        self.nav(Nav.DOWN, Nav.DOWN, Nav.UP)
        self.assertEqual(self.played, [])

    def test_left_right_do_nothing_on_buttons(self) -> None:
        self.nav(Nav.RIGHT)
        self.assertEqual((self.speaker.spoken, self.played), ([], []))

    def test_back(self) -> None:
        self.nav(Nav.BACK)
        self.assertTrue(self.backed)
        self.assertEqual(self.played, ["SFX_Back"])


if __name__ == "__main__":
    unittest.main()
