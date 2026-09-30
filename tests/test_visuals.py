import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from bopit import i18n
from bopit.visuals import BOPJECT_IMAGES, SCREEN_LAYOUTS, Renderer


class _Screen:
    def __init__(self, title: str) -> None:
        self.title = title


class VisualsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        cls.surface = pygame.display.set_mode((320, 480))

    def tearDown(self) -> None:
        i18n.set_language("en")

    def test_every_screen_draws_in_every_language(self) -> None:
        renderer = Renderer(self.surface)
        for code in ("en", "de", "es", "fr", "it"):
            i18n.set_language(code)
            for title in list(SCREEN_LAYOUTS) + ["Classic"]:
                for theme in (0, 1, 2):
                    renderer.draw(_Screen(title), theme, "caption", {})
                self.assertTrue(renderer.layout(renderer.layout_for(_Screen(title))), title)

    def test_intro_uses_the_intro_layout(self) -> None:
        self.assertEqual(Renderer.layout_for(_Screen("Blitz")), "GameModeIntro")

    def test_every_bopject_has_an_image(self) -> None:
        renderer = Renderer(self.surface)
        for command, name in BOPJECT_IMAGES.items():
            self.assertIsNotNone(renderer.image(name), command)
        renderer.bopjects({c: 4 for c in BOPJECT_IMAGES}, "Twist", 1)


if __name__ == "__main__":
    unittest.main()
