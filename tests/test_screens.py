import unittest

from bopit import screens
from bopit.config import Settings
from bopit.menu import Menu, Nav
from bopit.themes import themed
from tests.test_menu import RecordingSpeaker


class FakeNavigator:
    def __init__(self) -> None:
        self.settings = Settings()
        self.stack: list[Menu] = []
        self.not_built_calls: list[str] = []
        self.changes = 0
        self.played: list[str] = []
        self.music: list[str] = []
        self.quit_called = False

    def push(self, menu: Menu) -> None:
        self.stack.append(menu)

    def pop(self) -> None:
        self.stack.pop()

    def quit(self) -> None:
        self.quit_called = True

    def not_built(self, what: str) -> None:
        self.not_built_calls.append(what)

    def settings_changed(self) -> None:
        self.changes += 1

    def play(self, name: str) -> None:
        self.played.append(name)

    def play_themed(self, name: str) -> None:
        self.played.append(themed(name, self.settings.theme))

    def start_menu_music(self) -> None:
        self.music.append("start")

    def stop_menu_music(self) -> None:
        self.music.append("stop")


def labels(menu: Menu) -> list[str]:
    return [item.label for item in menu.items]


class ScreenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nav = FakeNavigator()
        self.speaker = RecordingSpeaker()
        self.nav.push(screens.main_menu(self.nav))

    def go(self, *moves: Nav) -> Menu:
        for move in moves:
            self.nav.stack[-1].handle(move, self.speaker, self.nav.play_themed)
        return self.nav.stack[-1]

    def open_settings(self) -> Menu:
        # Main menu: Options is third. Options: Settings is second.
        return self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT, Nav.DOWN, Nav.SELECT)

    def test_defaults_match_original(self) -> None:
        s = Settings()
        self.assertEqual((s.commands, s.banter, s.shout_it, s.music_volume, s.sfx_volume, s.theme),
                         ("VOX", True, True, 100, 60, 0))

    def test_order_matches_original_top_to_bottom(self) -> None:
        self.assertEqual(labels(self.nav.stack[-1]), ["Play", "Games", "Options", "Theme"])
        games = self.go(Nav.DOWN, Nav.SELECT)
        self.assertEqual(labels(games), ["Solo", "Multiplayer", "Trophies", "Scores"])
        solo = self.go(Nav.SELECT)
        self.assertEqual(labels(solo), ["Classic", "Basic", "Blitz", "Extreme"])
        self.go(Nav.BACK)
        multi = self.go(Nav.DOWN, Nav.SELECT)
        self.assertEqual(labels(multi), ["Pass It Basic", "Blitz Challenge", "Pass It Extreme", "Head 2 Head"])

    def test_options_and_settings(self) -> None:
        options = self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT)
        self.assertEqual(labels(options), ["Help", "Settings", "Credits", "About"])
        settings = self.go(Nav.DOWN, Nav.SELECT)
        self.assertEqual(labels(settings), ["Commands", "Banter", "Shout It", "Music", "SFX"])

    def test_button_sounds_match_original(self) -> None:
        self.go(Nav.DOWN, Nav.SELECT)  # Games: SFX_Select
        self.go(Nav.SELECT)  # Solo: SFX_Select
        self.go(Nav.SELECT)  # Classic: SFX_SelectGame
        self.go(Nav.BACK)  # SFX_Back
        self.assertEqual(self.nav.played, ["SFX_Select", "SFX_Select", "SFX_SelectGame", "SFX_Back"])

    def test_play_uses_select_game(self) -> None:
        self.go(Nav.SELECT)
        self.assertEqual(self.nav.played, ["SFX_SelectGame"])

    def test_button_sounds_follow_theme(self) -> None:
        self.go(Nav.LAST, Nav.RIGHT)
        self.assertEqual(self.nav.settings.theme, 1)
        self.assertEqual(self.nav.music, ["stop", "start"])
        self.go(Nav.FIRST, Nav.DOWN, Nav.SELECT)
        self.assertEqual(self.nav.played, ["SFX_Select_HLWN"])

    def test_theme_cycles_like_original(self) -> None:
        for expected in (1, 2, 0):
            self.go(Nav.LAST, Nav.RIGHT)
            self.assertEqual(self.nav.settings.theme, expected)

    def test_commands_previews(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.nav.music.clear()
        self.go(Nav.SELECT)  # VOX to SFX
        self.assertEqual((self.nav.played, self.nav.music), (["SFX_Bop_R"], ["start"]))
        self.go(Nav.SELECT)  # SFX to Silent
        self.assertEqual(self.nav.music, ["start", "stop"])
        self.go(Nav.SELECT)  # Silent to VOX
        self.assertEqual(self.nav.played, ["SFX_Bop_R", "VO_Bop"])

    def test_banter_and_shout_it_play_settings_select(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.go(Nav.DOWN, Nav.SELECT, Nav.DOWN, Nav.RIGHT)
        self.assertEqual(self.nav.played, ["SFX_SettingsSelect", "SFX_SettingsSelect"])
        self.assertEqual((self.nav.settings.banter, self.nav.settings.shout_it), (False, False))

    def test_sfx_slider_previews_except_in_silent(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.go(Nav.LAST, Nav.LEFT)
        self.assertEqual((self.nav.settings.sfx_volume, self.nav.played), (50, ["SFX_Bop_R"]))
        self.nav.settings.commands = "Silent"
        self.go(Nav.LEFT)
        self.assertEqual(self.nav.played, ["SFX_Bop_R"])

    def test_music_slider_is_silent(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.go(Nav.LAST, Nav.UP, Nav.LEFT)
        self.assertEqual((self.nav.settings.music_volume, self.nav.played), (90, []))

    def test_help_tabs_are_silent(self) -> None:
        self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT, Nav.SELECT)
        self.nav.played.clear()
        overview = self.go(Nav.SELECT)
        self.assertEqual((overview.title, self.nav.played), ("Overview", []))

    def test_back_on_main_menu_quits_silently(self) -> None:
        self.go(Nav.BACK)
        self.assertTrue(self.nav.quit_called)
        self.assertEqual(self.nav.played, [])

    def test_back_in_submenu_does_not_quit(self) -> None:
        self.go(Nav.DOWN, Nav.SELECT, Nav.BACK)
        self.assertFalse(self.nav.quit_called)
        self.assertEqual(len(self.nav.stack), 1)

    def test_about_shows_version(self) -> None:
        about = self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT, Nav.LAST, Nav.SELECT)
        self.assertEqual(about.title, "About")
        self.assertIn("v1.1.9", labels(about))


if __name__ == "__main__":
    unittest.main()
