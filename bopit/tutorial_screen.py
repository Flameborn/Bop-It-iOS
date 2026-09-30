"""The tutorial for one command (TutorialMode and GameViewController's tutorial view).

Top to bottom: the description, then Back, Demo and Try side by side. Try starts practice:
the game calls only this command, over and over, with the game music; mistakes do not end
it. While practicing, every key goes to the game and the pause key stops, like the
original's Try button turning into Stop. Demo (the question mark button, labelled "demo")
stops any practice and shows the demonstration again; here, as the demonstration was only
an animation, it reads the description again. None of these buttons made a sound.
"""

from bopit.engine.game import tutorial_rules
from bopit.game_screen import GameScreen, Host
from bopit.input_map import is_pause_key, is_score_key, menu_nav_for
from bopit.menu import Button, Menu
from bopit.tutorials import tutorial_text


class TutorialScreen:
    def __init__(self, host: Host, command: str) -> None:
        self.title = f"{command} tutorial"
        self._host = host
        self._command = command
        self._text = tutorial_text(command, host.settings.microphone)
        self._play: GameScreen | None = None
        self._entered = False
        self._try = Button("Try", self._toggle)
        self._menu = Menu(self.title, [
            Button(self._text, lambda: None),
            Button("Back", self._back),
            Button("Demo", self._again),
            self._try,
        ], on_back=self._back)
        self._now = 0.0

    @property
    def practicing(self) -> bool:
        return self._play is not None

    def enter(self, now: float) -> None:
        self._now = now
        if not self._entered:
            # TutorialMode's init (GameController::init) stopped the menu music.
            self._entered = True
            self._host.stop_menu_music()
        self._menu.enter(self._host.speech)

    def key(self, key: int, now: float) -> None:
        self._now = now
        if self._play is not None:
            if is_pause_key(key):
                self._stop()
                self._host.speech.speak("Stopped. " + self._menu.describe(), interrupt=True)
            elif not is_score_key(key):
                # The score was hidden during a tutorial.
                self._play.key(key, now)
            return
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._host.speech, self._host.play_themed)

    def update(self, now: float) -> None:
        self._now = now
        if self._play is not None:
            self._play.update(now)

    def caption(self) -> str:
        if self._play is not None:
            return self._play.caption()
        return self._menu.describe()

    def draw_game(self, renderer: "object", theme: int) -> None:
        if self._play is not None:
            self._play.draw_game(renderer, theme)
        else:
            renderer.bopjects({self._command: 4}, None, theme)

    def _toggle(self) -> None:
        if self._play is not None:
            self._stop()
            return
        # tutorialTryPressed: startGame straight away, with no "Bop It to start".
        self._try.label = "Stop"
        self._host.speech.speak("Practice. Escape to stop.", interrupt=True)
        self._play = GameScreen(self._host, tutorial_rules(self._command), start_now=True,
                                times_called={}, announce_start=False)
        self._play.enter(self._now)

    def _stop(self) -> None:
        """stopTutorial."""
        if self._play is not None:
            self._play.stop(self._now)
            self._play = None
        self._try.label = "Try"

    def _again(self) -> None:
        """tutorialPlayPressed: stop, and show the demonstration again."""
        self._stop()
        self._host.speech.speak(self._text, interrupt=True)

    def _back(self) -> None:
        """tutorialBackPressed: stop, then back to Help, or into the game mode it came
        from."""
        self._stop()
        self._host.tutorial_back()
