"""Build the translation catalogs from the original app's own translations.

Usage: python tools/extract_texts.py

For German, Spanish, French and Italian, each English text the original showed is paired
with its translation, from two sources:
- Localizable.strings: the same key in English.lproj and the language's folder.
- The nibs: each English nib and its translated copy, walked view by view in screen order.
  A few translated nibs have an extra view, so the two walks are aligned by view class.

The catalogs are written to bopit/lang/<language>.json as {English: translation}. When one
English text had different translations in different places, the first found is kept and
the others are reported.
"""

import difflib
import json
import plistlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dump_nib import Nib  # noqa: E402

from bopit.config import ORIGINAL_APP_DIR, PROJECT_ROOT  # noqa: E402

LANGUAGES = ("de", "es", "fr", "it")
OUT_DIR = PROJECT_ROOT / "bopit" / "lang"

# Labels the original built from two or more pieces of text, which the port reads as one.
# Each is put together from the translated pieces, in screen order, as the original
# showed them. These win over anything paired automatically.
COMPOSED: dict[str, dict[str, str]] = {
    # LandingPage::setPlayButtonLabel: "Quick" over "Play" (Localizable.strings).
    "Quick Play": {"de": "Schnelles Spiel", "es": "partida rápida",
                   "fr": "partie rapide", "it": "partita rapida"},
    # LandingPage::setPlayButtonLabel: "resume" over "game" (Localizable.strings).
    "Resume Game": {"de": "Spiel Fortsetzen", "es": "reanudar partida",
                    "fr": "reprendre partie", "it": "riprendi partita"},
    # The end screens: "play" over "again".
    "Play again": {"de": "Erneut spielen", "es": "volver a jugar", "fr": "rejouer",
                   "it": "gioca ancora"},
    # GamesPage: "multi" over "player".
    "Multiplayer": {"de": "Multi Player", "es": "multijugador", "fr": "multi joueur",
                    "it": "multi player"},
    # CommandPicker: "customize" over "game".
    "customize game": {"de": "Spiel anpassen", "es": "Personalizar juego",
                       "fr": "personnaliser partie", "it": "personalizza gioco"},
    # GameViewController's help popup and tutorial buttons.
    "Continue": {"de": "Weiter", "es": "continuar", "fr": "continuer", "it": "continua"},
    "Try it": {"de": "Testen", "es": "pruébalo", "fr": "essaye", "it": "prova"},
    "Try": {"de": "Test", "es": "prueba", "fr": "essayer", "it": "prova"},
    "Demo": {"de": "Demo", "es": "demo", "fr": "démo", "it": "demo"},
    # MPBlitzBreak's GO button, labelled "next".
    "Next": {"de": "Weiter", "es": "siguiente", "fr": "suivant", "it": "avanti"},
    # GameModeIntro's START.
    "Start": {"de": "Starten", "es": "EMPEZAR", "fr": "COMMENCER", "it": "INIZIA"},
    # The pieces above paired wrongly on their own; these are the whole words.
    "Play": {"de": "Spiel", "es": "jugar", "fr": "jouer", "it": "gioca"},
    "Resume": {"de": "Fortsetzen", "es": "reanudar", "fr": "reprendre", "it": "riprendi"},
    "Multi Player": {"de": "Multi Player", "es": "multijugador", "fr": "multi joueur",
                     "it": "multiplayer"},
}


def read_strings(path: Path) -> dict[str, str]:
    raw = path.read_bytes()
    try:
        data = plistlib.loads(raw)
        return {str(k): str(v) for k, v in data.items()}
    except Exception:
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
        return dict(re.findall(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', text))


def nib_views(nib: Nib) -> list[tuple[str, str | None]]:
    """(class, text or button title) for each view, in screen tree order."""
    out: list[tuple[str, str | None]] = []

    def walk(uid) -> None:
        obj = nib.get(uid)
        text = None
        if isinstance(obj, dict):
            if obj.get("UIText") is not None:
                text = str(nib.get(obj["UIText"]))
            else:
                text = nib.button_content(obj).get("title")
        out.append((nib.class_name(obj), text))
        if isinstance(obj, dict) and "UISubviews" in obj:
            for child in nib.array(obj["UISubviews"]):
                walk(child)

    for uid in nib.array(nib.top["UINibTopLevelObjectsKey"]):
        if nib.class_name(nib.get(uid)) != "UIProxyObject":
            walk(uid)
    return out


def usable(text: str | None) -> bool:
    return bool(text) and bool(text.strip()) and text.strip() != "Label"


class Catalog:
    def __init__(self) -> None:
        self.pairs: dict[str, str] = {}
        self.conflicts: list[str] = []

    def add(self, english: str | None, translated: str | None, where: str) -> None:
        if not usable(english) or not usable(translated):
            return
        if "\n" in english.strip() and "\n" in translated.strip():
            # A whole text block (Help, Credits, About): pair it line by line when the
            # translation has the same number of lines.
            a, b = english.strip().split("\n"), translated.strip().split("\n")
            if len(a) == len(b):
                for x, y in zip(a, b):
                    self.add(x, y, where)
                return
        english, translated = english.strip(), translated.strip()
        known = self.pairs.get(english)
        if known is None:
            self.pairs[english] = translated
        elif known != translated:
            self.conflicts.append(f"{where}: {english!r} is {known!r} and {translated!r}")


def build(language: str) -> Catalog:
    catalog = Catalog()
    english_dir = ORIGINAL_APP_DIR / "English.lproj"
    language_dir = ORIGINAL_APP_DIR / f"{language}.lproj"

    english_strings = read_strings(english_dir / "Localizable.strings")
    translated_strings = read_strings(language_dir / "Localizable.strings")
    for key, english in english_strings.items():
        if key in translated_strings:
            catalog.add(english, translated_strings[key], "Localizable.strings")

    for english_nib in sorted(english_dir.glob("*.nib")):
        translated_nib = language_dir / english_nib.name
        if not translated_nib.exists():
            continue
        a = nib_views(Nib(english_nib))
        b = nib_views(Nib(translated_nib))
        matcher = difflib.SequenceMatcher(a=[c for c, _ in a], b=[c for c, _ in b],
                                          autojunk=False)
        for block in matcher.get_matching_blocks():
            for i in range(block.size):
                catalog.add(a[block.a + i][1], b[block.b + i][1], english_nib.name)
    for english, translations in COMPOSED.items():
        catalog.pairs[english] = translations[language]
    return catalog


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for language in LANGUAGES:
        catalog = build(language)
        path = OUT_DIR / f"{language}.json"
        path.write_text(json.dumps(catalog.pairs, ensure_ascii=False, indent=1, sort_keys=True)
                        + "\n", encoding="utf-8")
        print(f"{language}: {len(catalog.pairs)} texts, {len(catalog.conflicts)} conflicts")
        for conflict in catalog.conflicts:
            print(f"  {conflict}")


if __name__ == "__main__":
    main()
