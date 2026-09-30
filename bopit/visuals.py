"""The picture on the screen. Lowest priority (see docs/DEVIATIONS.md): each screen is drawn
from the original's layout and images, without its animations or exact fonts, and the
focused menu item is shown in a caption strip for anyone watching. Nothing here affects
play, speech or sound, and any missing image is simply skipped.

Layouts come from tools/extract_layouts.py (layouts/<language>/<Nib>.json) and images from
tools/extract_images.py (images/, and images/<language>/ for images with words in them).
"""

import json
import logging
import re
from pathlib import Path

import pygame

from bopit import i18n
from bopit.config import PROJECT_ROOT
from bopit.screens import MODE_DESCRIPTIONS
from bopit.themes import themed

log = logging.getLogger(__name__)

IMAGES_DIR = PROJECT_ROOT / "images"
LAYOUTS_DIR = PROJECT_ROOT / "layouts"
SIZE = (320, 480)
DEFAULT_TEXT_SIZE = 16
TEXT_COLOUR = (255, 255, 255)
SHADOW_COLOUR = (0, 0, 0)
HIGHLIGHT_COLOUR = (255, 220, 0)

# Which of the original's screens each port screen is, by its (English) title.
SCREEN_LAYOUTS = {
    "Bop It": "LandingPage", "Games": "GamesPage", "Solo": "SoloGameOptions",
    "Multiplayer": "MultiPlayerOptions", "Options": "OptionsPage", "Settings": "Settings",
    "Help": "Help", "Tutorials": "Help", "Overview": "Help", "Keys": "Help",
    "Credits": "Credits", "About": "About", "Scores": "Scores", "Trophies": "TrophiesPage",
    "customize game": "CommandPicker", "Blitz Challenge players": "mpBlitzPlayerSelect",
    "Paused": "PauseMenu", "Game over": "SoloEndGame", "Finished": "SoloBlitzEndGame",
    "Results": "MPBlitzEndGame", "Winner": "MPH2HEndGame", "Break": "MPBlitzBreak",
    "Would you like to see the tutorials and try the moves before playing?": "TutorialPopUp",
}
MODE_INTRO_LAYOUT = "GameModeIntro"
# Images the original's code put in place, by outlet, as its viewDidLoad methods did.
CODE_IMAGES = {
    "backgroundImage": "gameOptions_background.jpg",
    "bopItLogo": "soloEndGame_bopitLogo.png",
}
CODE_IMAGES_BY_LAYOUT = {
    "CommandPicker": {"bopitButtonImage": "multiGameCustom_bopjectBopIt.png"},
    "Help": {"bopitButtonImage": "help_bopjectBopIt.png"},
}
# The main menu's background and logo, which its code added.
LANDING_EXTRAS = (("landingPage_background.png", (0, 0, 320, 480)),
                  ("landingPage_bopitLogo.png", (12, 30, 295, 170)))
# Things this port leaves out (the More Games button); labels on them go too.
HIDDEN_IMAGES = {"landingPage_moreGamesBtn.png"}
# Sample text in the layouts that the original's code always replaced.
PLACEHOLDER = re.compile(r"^[\d.,:s ]+$|^Label$|Player 1 Time")

# The game screen (GameViewController): where each location's BopJect sits, as
# (centre x, centre y) of its command view (getCommandView:).
LOCATION_CENTRES = {0: (108, 171), 1: (214.5, 171), 2: (108, 343), 3: (214.5, 343),
                    4: (160, 240), 5: (160, 257)}
BOPJECT_IMAGES = {
    "Bop": "Bop320X480_0.png", "Brush": "Brush320X480_0.png", "Crank": "Crank320x480_0.png",
    "Flick": "Flick320x480_0.png", "Nail": "Nail320X480_0.png", "Poke": "Poke320X480_0.png",
    "Pull": "Pull320X480_0.png", "Shake": "Shake320X480_0.png", "Shout": "Shout320X480_0.png",
    "Spin": "Spin320X480_0.png", "Squeeze": "Squeeze320X480_0.png",
    "Twist": "Twist320x480_0.png",
}
GAME_BACKGROUND = "soloInGame_background1.jpg"


class Renderer:
    def __init__(self, surface: pygame.Surface) -> None:
        self._surface = surface
        self._images: dict[tuple[str, str, int], pygame.Surface | None] = {}
        self._layouts: dict[tuple[str, str], list[dict]] = {}
        self._fonts: dict[int, pygame.font.Font] = {}
        # Rendered text and scaled images, so drawing a frame is only blitting.
        self._texts: dict[tuple, list[tuple[pygame.Surface, tuple[float, float]]]] = {}
        self._scaled: dict[tuple, pygame.Surface] = {}
        self._captions: dict[tuple, tuple[pygame.Surface, list]] = {}
        self._caption_fonts: dict[int, pygame.font.Font] = {}

    # Loading

    def image(self, name: str, theme: int = 0) -> pygame.Surface | None:
        """An image by the original's name: the theme's variant if there is one, the
        language's own copy if there is one, else the shared one."""
        language = i18n.language()
        key = (name, language, theme)
        if key not in self._images:
            self._images[key] = self._load(name, language, theme)
        return self._images[key]

    def _load(self, name: str, language: str, theme: int) -> pygame.Surface | None:
        stem, suffix = Path(name).stem, Path(name).suffix
        candidates = []
        if theme:
            variant = themed(stem, theme)
            candidates += [f"{variant}{suffix}", f"{variant}.png", f"{variant}.jpg"]
        candidates.append(name)
        for candidate in candidates:
            for folder in (IMAGES_DIR / language, IMAGES_DIR):
                path = folder / candidate
                if path.exists():
                    try:
                        return pygame.image.load(str(path)).convert_alpha()
                    except pygame.error:
                        log.warning("Could not load image %s", path)
        return None

    def layout(self, name: str) -> list[dict]:
        language = i18n.language()
        key = (name, language)
        if key not in self._layouts:
            path = LAYOUTS_DIR / language / f"{name}.json"
            try:
                self._layouts[key] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._layouts[key] = []
        return self._layouts[key]

    def font(self, size: int) -> pygame.font.Font:
        size = max(10, min(size, 48))
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    # Drawing

    def draw(self, screen: object, theme: int, caption: str | None,
             texts: dict[str, str] | None = None, text_size: int = DEFAULT_TEXT_SIZE) -> None:
        self._surface.fill((0, 0, 0))
        name = self.layout_for(screen)
        if name is not None:
            self.draw_layout(name, theme, texts or {})
        draw_game = getattr(screen, "draw_game", None)
        if draw_game is not None:
            draw_game(self, theme)
        if caption:
            self.caption(caption, text_size)

    @staticmethod
    def layout_for(screen: object) -> str | None:
        title = getattr(screen, "title", "")
        if title in MODE_DESCRIPTIONS:
            # A mode's intro is titled with the mode's name.
            return MODE_INTRO_LAYOUT
        return SCREEN_LAYOUTS.get(title)

    def draw_layout(self, name: str, theme: int, texts: dict[str, str]) -> None:
        if name == MODE_INTRO_LAYOUT:
            # The intro was a panel over the game screen.
            self.blit(GAME_BACKGROUND, theme, pygame.Rect(0, 0, *SIZE))
        if name == "LandingPage":
            for image, rect in LANDING_EXTRAS:
                self.blit(image, theme, pygame.Rect(rect))
        elements = self.layout(name)
        hidden = [pygame.Rect(e["rect"]) for e in elements if e.get("image") in HIDDEN_IMAGES]
        code_images = dict(CODE_IMAGES, **CODE_IMAGES_BY_LAYOUT.get(name, {}))
        for element in elements:
            rect = pygame.Rect(element["rect"])
            if any(h.collidepoint(rect.center) for h in hidden):
                continue
            image = element.get("image") or code_images.get(element.get("outlet", ""))
            if image:
                self.blit(image, theme, rect)
            if element.get("foreground"):
                self.blit(element["foreground"], theme, rect)
            text = texts.get(element.get("outlet", ""), element.get("text"))
            if text and not PLACEHOLDER.search(text):
                self.text(text, rect)

    def blit(self, name: str, theme: int, rect: pygame.Rect, centred: bool = True) -> None:
        image = self.image(name, theme)
        if image is None:
            return
        if image.get_size() != rect.size and rect.width and rect.height:
            if image.get_width() >= 300 and rect.width >= 300:
                key = (name, theme, rect.size)
                if key not in self._scaled:
                    self._scaled[key] = pygame.transform.smoothscale(image, rect.size)
                image = self._scaled[key]
        position = image.get_rect(center=rect.center) if centred else rect.topleft
        self._surface.blit(image, position)

    def wrap(self, text: str, rect: pygame.Rect) -> tuple[pygame.font.Font, list[str]]:
        """The largest font, up to one line's worth of the box, whose word-wrapped lines fit
        the box."""
        paragraphs = text.split("\n")
        start = int(min(rect.height / max(len(paragraphs), 1) * 0.8, 36))
        lines: list[str] = []
        for size in range(start, 9, -1):
            font = self.font(size)
            lines = []
            for paragraph in paragraphs:
                line = ""
                for word in paragraph.split(" "):
                    trial = f"{line} {word}".strip()
                    if line and font.size(trial)[0] > rect.width:
                        lines.append(line)
                        line = word
                    else:
                        line = trial
                lines.append(line)
            if font.get_linesize() * len(lines) <= rect.height:
                return font, lines
        return self.font(10), lines

    def text(self, text: str, rect: pygame.Rect, colour: tuple[int, int, int] = TEXT_COLOUR) -> None:
        key = (text, tuple(rect), colour)
        pieces = self._texts.get(key)
        if pieces is None:
            pieces = self._texts[key] = self._render_text(text, rect, colour)
        for surface, position in pieces:
            self._surface.blit(surface, position)

    def _render_text(self, text: str, rect: pygame.Rect,
                     colour: tuple[int, int, int]) -> list[tuple[pygame.Surface, tuple[float, float]]]:
        font, lines = self.wrap(text, rect)
        pieces = []
        y = rect.centery - font.get_linesize() * len(lines) / 2
        for line in lines:
            rendered = font.render(line, True, colour)
            if rendered.get_width() > rect.width > 0:
                scale = rect.width / rendered.get_width()
                rendered = pygame.transform.smoothscale(
                    rendered, (rect.width, max(1, int(rendered.get_height() * scale))))
            shadow = pygame.transform.smoothscale(font.render(line, True, SHADOW_COLOUR),
                                                  rendered.get_size())
            # Keep it on the screen, even where the original let a long word spill over.
            x = min(max(rect.centerx - rendered.get_width() / 2, 0),
                    SIZE[0] - rendered.get_width())
            pieces.append((shadow, (x + 1, y + 1)))
            pieces.append((rendered, (x, y)))
            y += font.get_linesize()
        return pieces

    def caption(self, text: str, points: int = DEFAULT_TEXT_SIZE) -> None:
        """The caption strip along the bottom, in the Text size setting's size. Long text
        wraps, and the strip grows to fit it, up to half the screen."""
        key = (text, points)
        pieces = self._captions.get(key)
        if pieces is None:
            pieces = self._captions[key] = self._render_caption(text, points)
        strip, lines = pieces
        top = SIZE[1] - strip.get_height()
        self._surface.blit(strip, (0, top))
        for surface, (x, y) in lines:
            self._surface.blit(surface, (x, top + y))

    def _render_caption(self, text: str, points: int) -> tuple[pygame.Surface, list]:
        font = self.caption_font(points)
        width = SIZE[0] - 8
        lines: list[str] = []
        line = ""
        for word in text.split(" "):
            trial = f"{line} {word}".strip()
            if line and font.size(trial)[0] > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        max_lines = max(1, (SIZE[1] // 2 - 4) // font.get_linesize())
        lines = lines[:max_lines]
        height = font.get_linesize() * len(lines) + 4
        strip = pygame.Surface((SIZE[0], height), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 190))
        rendered = []
        y = 2
        for line in lines:
            surface = font.render(line, True, HIGHLIGHT_COLOUR)
            if surface.get_width() > width:
                surface = pygame.transform.smoothscale(
                    surface, (width, max(1, surface.get_height() * width // surface.get_width())))
            rendered.append((surface, ((SIZE[0] - surface.get_width()) / 2, y)))
            y += font.get_linesize()
        return strip, rendered

    def caption_font(self, points: int) -> pygame.font.Font:
        # pygame's default font runs small, so a point is taken as four thirds of its units.
        size = round(points * 4 / 3)
        if size not in self._caption_fonts:
            self._caption_fonts[size] = pygame.font.Font(None, size)
        return self._caption_fonts[size]

    def bopjects(self, locations: dict[str, int], current: str | None, theme: int) -> None:
        """The game screen: background, each active BopJect in its place, and a frame
        round the one being called."""
        self.blit(GAME_BACKGROUND, theme, pygame.Rect(0, 0, *SIZE))
        for command, location in locations.items():
            name = BOPJECT_IMAGES.get(command)
            centre = LOCATION_CENTRES.get(location, LOCATION_CENTRES[4])
            image = self.image(name, theme) if name else None
            if image is None:
                continue
            rect = image.get_rect(center=centre)
            self._surface.blit(image, rect)
            if command == current:
                pygame.draw.rect(self._surface, HIGHLIGHT_COLOUR, rect.inflate(-20, -20), 3,
                                 border_radius=12)
