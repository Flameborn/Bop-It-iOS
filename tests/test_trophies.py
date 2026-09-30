import random
import unittest

from bopit.tips import ALL_TIPS, TIP_CHANCE, Tips
from bopit.trophies import all_trophies, newly_earned


class TrophyListTests(unittest.TestCase):
    def test_order_and_count(self) -> None:
        trophies = all_trophies(shout_it=True)
        titles = [t.title for t in trophies]
        self.assertEqual(titles[0], "Spin to Win! Spin Unlocked")
        self.assertEqual(titles[8], "Yowch! Poke Unlocked")
        self.assertEqual(titles[9:12], ["Got to 50!", "Got to 100!", "Got to 200!"])
        self.assertEqual(titles[12:16], ["Did 10 X-Moves", "Did 25 X-Moves!", "Did 50 X-Moves!!",
                                         "Did 100 X-Moves!!!"])
        self.assertEqual(titles[16:18], ["100 Bops", "500 Bops!!"])
        self.assertEqual(titles[-3:], ["Blitzed It under 25s", "Blitzed It under 30s",
                                       "Blitzed It under 35s"])
        self.assertEqual(len(trophies), 9 + 3 + 4 + 24 + 3)

    def test_shout_off_drops_its_lifetime_trophies(self) -> None:
        titles = [t.title for t in all_trophies(shout_it=False)]
        self.assertNotIn("100 Shouts", titles)
        self.assertIn("Yeah! Shout Unlocked", titles)

    def test_medals(self) -> None:
        medals = {t.title: t.medal for t in all_trophies(True)}
        self.assertEqual((medals["Spin to Win! Spin Unlocked"], medals["Hamma Time! Nail Unlocked"]),
                         ("bronze", "gold"))
        self.assertEqual((medals["100 Bops"], medals["500 Bops!!"]), ("silver", "gold"))
        self.assertEqual(medals["Blitzed It under 35s"], "bronze")


class TrophyCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trophies = all_trophies(True)

    def titles(self, **kwargs) -> list[str]:
        base = {"earned": set(), "moves": 0, "x_moves": 0, "hits": {}}
        base.update(kwargs)
        return [t.title for t in newly_earned(self.trophies, base["earned"], base["moves"],
                                               base["x_moves"], base["hits"], base.get("blitz_time"))]

    def test_moves_in_a_game(self) -> None:
        self.assertEqual(self.titles(moves=100), ["Got to 50!", "Got to 100!"])

    def test_x_moves(self) -> None:
        self.assertEqual(self.titles(x_moves=25), ["Did 10 X-Moves", "Did 25 X-Moves!"])

    def test_lifetime(self) -> None:
        self.assertEqual(self.titles(hits={"Twist": 500}), ["100 Twists", "500 Twists!!"])

    def test_blitz_needs_finish(self) -> None:
        self.assertEqual(self.titles(moves=20, blitz_time=28.0),
                         ["Blitzed It under 30s", "Blitzed It under 35s"])
        self.assertEqual(self.titles(moves=19, blitz_time=20.0), [])

    def test_already_earned_skipped(self) -> None:
        self.assertEqual(self.titles(moves=60, earned={"Got to 50!"}), [])


class TipTests(unittest.TestCase):
    def test_chance_and_no_repeats(self) -> None:
        tips = Tips(ALL_TIPS, random.Random(4))
        shown = [t for t in (tips.maybe_tip() for _ in range(2000)) if t is not None]
        self.assertAlmostEqual(len(shown) / 2000, TIP_CHANCE / 100, delta=0.04)
        first_round = shown[:len(ALL_TIPS)]
        self.assertEqual(len(set(first_round)), len(ALL_TIPS))


if __name__ == "__main__":
    unittest.main()
