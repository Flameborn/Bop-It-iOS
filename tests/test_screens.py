import tempfile
import unittest
from pathlib import Path

from bopit import screens
from bopit.config import Settings
from bopit.progress import Progress
from bopit.scores import Scores
from bopit.menu import Menu, Nav
from bopit.themes import themed
from tests.test_menu import RecordingSpeaker


class FakeNavigator:
    def __init__(self) -> None:
        self.settings = Settings()
        self._tmp = tempfile.TemporaryDirectory()
        self.scores = Scores(Path(self._tmp.name) / "scores.json")
        self.progress = Progress(Path(self._tmp.name) / "progress.json")
        self.stack: list[Menu] = []
        self.not_built_calls: list[str] = []
        self.changes = 0
        self.played: list[str] = []
        self.music: list[str] = []
        self.quit_called = False
        self.saved = False
        # Pretend the one-time hints were already seen, unless a test clears this.
        self.seen: set[str] = {"quick_play_hint"}
        self.spoken: list[str] = []

    def push(self, menu: Menu) -> None:
        self.stack.append(menu)

    def pop(self) -> None:
        self.stack.pop()

    def quit(self) -> None:
        self.quit_called = True

    def start_mode(self, name: str) -> None:
        self.not_built_calls.append(name)

    def has_saved_game(self) -> bool:
        return self.saved

    def first_time(self, flag: str) -> bool:
        if flag in self.seen:
            return False
        self.seen.add(flag)
        return True

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def play_pressed(self) -> None:
        self.not_built_calls.append("play")

    def return_to_menu(self) -> None:
        del self.stack[1:]

    def not_built(self, what: str) -> None:
        self.not_built_calls.append(what)

    def settings_changed(self) -> None:
        self.changes += 1

    def language_changed(self) -> None:
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
        self.assertTrue(s.microphone)

    def test_order_matches_original_top_to_bottom(self) -> None:
        self.assertEqual(labels(self.nav.stack[-1]), ["Quick Play", "Games", "Options", "Theme"])
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
        self.assertEqual(labels(settings), ["Commands", "Banter", "Shout It", "Music", "SFX", "Microphone",
                                           "Language", "Text size"])

    def test_button_sounds_match_original(self) -> None:
        self.go(Nav.DOWN, Nav.SELECT)  # Games: SFX_Select
        self.go(Nav.SELECT)  # Solo: SFX_Select
        self.go(Nav.SELECT)  # Classic is a hold button: it acts on a quick release.
        self.nav.stack[-1].release(Nav.SELECT, self.nav.play_themed, 0.1)  # SFX_SelectGame
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
        self.go(Nav.SELECT)  # SFX back to VOX, as Silent is not offered
        self.assertEqual(self.nav.played, ["SFX_Bop_R", "VO_Bop"])
        self.assertEqual(self.nav.settings.commands, "VOX")

    def test_banter_and_shout_it_play_settings_select(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.go(Nav.DOWN, Nav.SELECT, Nav.DOWN, Nav.RIGHT)
        self.assertEqual(self.nav.played, ["SFX_SettingsSelect", "SFX_SettingsSelect"])
        self.assertEqual((self.nav.settings.banter, self.nav.settings.shout_it), (False, False))

    def test_sfx_slider_previews_except_in_silent(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.focus("SFX"); self.go(Nav.LEFT)
        self.assertEqual((self.nav.settings.sfx_volume, self.nav.played), (50, ["SFX_Bop_R"]))
        self.nav.settings.commands = "Silent"
        self.go(Nav.LEFT)
        self.assertEqual(self.nav.played, ["SFX_Bop_R"])

    def test_music_slider_is_silent(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.focus("Music"); self.go(Nav.LEFT)
        self.assertEqual((self.nav.settings.music_volume, self.nav.played), (90, []))

    def test_microphone_toggle(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.focus("Microphone"); self.go(Nav.SELECT)
        self.assertFalse(self.nav.settings.microphone)
        self.assertEqual(self.nav.played, ["SFX_SettingsSelect"])

    def test_language_choice(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.focus("Language"); self.go(Nav.RIGHT)
        self.assertEqual(self.nav.settings.language, "de")
        self.assertEqual(self.nav.played, ["SFX_SettingsSelect"])

    def test_text_size_slider(self) -> None:
        self.open_settings()
        self.nav.played.clear()
        self.focus("Text size")
        self.go(Nav.RIGHT)
        self.assertEqual(self.nav.settings.text_size, 18)
        for _ in range(20):
            self.go(Nav.LEFT)
        self.assertEqual(self.nav.settings.text_size, 12)
        for _ in range(20):
            self.go(Nav.RIGHT)
        self.assertEqual(self.nav.settings.text_size, 32)
        self.assertEqual(self.nav.played, [])

    def focus(self, label: str) -> None:
        """Move the focus to a settings item by name."""
        menu = self.nav.stack[-1]
        menu.focus = [item.label for item in menu.items].index(label)

    def test_help_tabs_are_silent(self) -> None:
        self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT, Nav.SELECT)
        self.nav.played.clear()
        overview = self.go(Nav.SELECT)
        self.assertEqual((overview.title, self.nav.played), ("Overview", []))

    def solo(self) -> Menu:
        return self.go(Nav.DOWN, Nav.SELECT, Nav.SELECT)

    def test_short_press_starts_mode(self) -> None:
        solo = self.solo()
        solo.handle(Nav.DOWN, self.speaker, self.nav.play_themed, 10.0)
        solo.handle(Nav.SELECT, self.speaker, self.nav.play_themed, 10.0)
        self.assertEqual(self.nav.not_built_calls, [])
        solo.release(Nav.SELECT, self.nav.play_themed, 10.5)
        self.assertEqual(self.nav.not_built_calls, ["Basic"])

    def test_hold_sets_quick_play(self) -> None:
        solo = self.solo()
        self.nav.played.clear()
        solo.handle(Nav.SELECT, self.speaker, self.nav.play_themed, 10.0)
        solo.update(11.19)
        self.assertEqual(self.nav.settings.quick_play, "Basic")
        solo.update(11.21)
        self.assertEqual(self.nav.settings.quick_play, "Classic")
        self.assertEqual(self.nav.played, ["SFX_SelectGame"])
        self.assertEqual(self.nav.spoken, ["Classic is now your Quick Play game."])
        solo.release(Nav.SELECT, self.nav.play_themed, 12.0)
        self.assertEqual(self.nav.not_built_calls, [])
        self.assertEqual(solo.describe(0), "Classic, Quick Play, 1 of 4")

    def test_release_between_tap_and_hold_does_nothing(self) -> None:
        solo = self.solo()
        solo.handle(Nav.SELECT, self.speaker, self.nav.play_themed, 10.0)
        solo.update(11.15)
        solo.release(Nav.SELECT, self.nav.play_themed, 11.15)
        self.assertEqual((self.nav.not_built_calls, self.nav.settings.quick_play), ([], "Basic"))

    def test_first_solo_visit_shows_quick_play_hint(self) -> None:
        self.nav.seen.clear()
        hint = self.go(Nav.DOWN, Nav.SELECT, Nav.SELECT)
        self.assertTrue(hint.title.startswith("Press and hold Enter"))
        closed = self.go(Nav.SELECT)
        self.assertEqual(closed.title, "Solo")
        self.go(Nav.BACK, Nav.SELECT)
        self.assertEqual(self.nav.stack[-1].title, "Solo")

    def open_scores(self) -> Menu:
        return self.go(Nav.DOWN, Nav.SELECT, Nav.LAST, Nav.SELECT)

    def test_scores_rows(self) -> None:
        self.nav.scores.add("Classic", 2222, 22)
        self.nav.scores.add("Classic", 505, 5)
        self.nav.scores.add_time("Blitz", 23.31)
        scores = self.open_scores()
        self.assertEqual(labels(scores), ["Mode", "Me, 22 moves, 2,222 points", "Me, 5 moves, 505 points", "Reset"])
        self.go(Nav.LEFT)  # wraps from Classic to Blitz
        self.assertEqual(labels(scores), ["Mode", "Me, 23.310 seconds", "Reset"])
        self.go(Nav.LEFT)
        self.assertEqual(labels(scores), ["Mode", "No scores", "Reset"])

    def test_scores_reset_cancel_and_ok(self) -> None:
        self.nav.scores.add("Classic", 2222, 22)
        self.open_scores()
        question = self.go(Nav.LAST, Nav.SELECT)
        self.assertTrue(question.title.startswith("Whoa!"))
        self.go(Nav.SELECT)  # Cancel
        self.assertEqual(self.nav.scores.best("Classic").score, 2222)
        self.go(Nav.LAST, Nav.SELECT, Nav.DOWN, Nav.SELECT)  # OK
        self.assertEqual(self.nav.stack[-1].title, "Scores")
        self.assertEqual(labels(self.nav.stack[-1]), ["Mode", "No scores", "Reset"])

    def test_trophies_page(self) -> None:
        self.nav.progress.unlock("Spin")
        self.nav.progress.earn(["Got to 50!"])
        trophies = self.go(Nav.DOWN, Nav.SELECT, Nav.DOWN, Nav.DOWN, Nav.SELECT)
        self.assertEqual(trophies.title, "Trophies")
        self.assertEqual(trophies.describe(0), "Spin to Win! Spin Unlocked, bronze trophy, 1 of 43")
        self.assertEqual(trophies.describe(1), "Boiiinng! Flick Unlocked, locked, 2 of 43")
        self.assertEqual(trophies.describe(9), "Got to 50!, bronze trophy, 10 of 43")

    def picker(self, mode: str = "Pass It Basic") -> Menu:
        self.chosen: list[tuple[str, ...]] = []
        menu = screens.picker_menu(self.nav, mode, self.chosen.append)
        self.nav.push(menu)
        return menu

    def test_picker_defaults_and_order(self) -> None:
        menu = self.picker()
        self.assertEqual(labels(menu)[:3], ["GO", "Bop It", "Twist"])
        self.assertEqual(labels(menu)[-1], "Add 2-4 BopJects to Bop It")
        self.assertEqual(menu.describe(2), "Twist, on, 3 of 14")
        self.assertEqual(menu.describe(4), "Spin, locked, 5 of 14")

    def test_picker_unlocked_defaults(self) -> None:
        self.nav.progress.unlock("Spin")
        self.nav.progress.unlock("Flick")
        menu = self.picker()
        self.assertEqual(menu.describe(4), "Spin, on, 5 of 14")
        self.go(Nav.SELECT)
        self.assertEqual(self.chosen, [("Twist", "Pull", "Spin", "Flick")])

    def test_picker_toggle_sounds_and_go_needs_two(self) -> None:
        self.picker()
        self.nav.played.clear()
        self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT)  # Twist off
        self.assertEqual(self.nav.played, ["SFX_BackButtonOLD"])
        self.assertEqual(self.nav.stack[-1].describe(0), "GO, unavailable, 1 of 14")
        self.go(Nav.FIRST, Nav.SELECT)
        self.assertEqual(self.chosen, [])
        self.go(Nav.DOWN, Nav.DOWN, Nav.SELECT)  # Twist on again
        self.assertEqual(self.nav.played[-1], "SFX_SettingsSelect")
        self.go(Nav.FIRST, Nav.SELECT)
        self.assertEqual(self.chosen, [("Twist", "Pull")])
        self.assertEqual(self.nav.settings.picked, ["Twist", "Pull"])

    def test_picker_max_four_and_poke_in_head_2_head(self) -> None:
        for c in ("Spin", "Flick", "Shout", "Poke"):
            self.nav.progress.unlock(c)
        menu = self.picker("Head 2 Head")
        self.assertEqual(menu.describe(12), "Poke, locked, 13 of 14")
        self.go(Nav.DOWN, Nav.DOWN, Nav.DOWN, Nav.DOWN, Nav.DOWN, Nav.DOWN, Nav.SELECT)  # Shout
        self.assertEqual(self.nav.spoken[-1], "4 already chosen.")

    def test_play_reads_resume_game_with_a_save(self) -> None:
        self.nav.saved = True
        self.assertEqual(labels(screens.main_menu(self.nav))[0], "Resume Game")

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
