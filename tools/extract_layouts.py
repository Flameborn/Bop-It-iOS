"""Turn the original's screen layouts (nibs) into simple drawing lists in layouts/.

Usage: python tools/extract_layouts.py

For each nib in each language folder, every visible image, button and text is written in
drawing order (back to front) with its screen rectangle in 320 by 480 points, to
layouts/<code>/<Nib>.json. Hidden views and everything inside them are left out, as they
were popups shown only in certain moments. Outlet names are kept, so the game can find an
element (for example the Play button's label) to change its text.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dump_nib import Nib  # noqa: E402

from bopit.config import ORIGINAL_APP_DIR, PROJECT_ROOT  # noqa: E402

LAYOUTS_DIR = PROJECT_ROOT / "layouts"
LANGUAGE_FOLDERS = {"English.lproj": "en", "de.lproj": "de", "es.lproj": "es",
                    "fr.lproj": "fr", "it.lproj": "it"}
TEXT_CLASSES = ("FontLabel", "UILabel")


def outlet_names(nib: Nib) -> dict[int, str]:
    names: dict[int, str] = {}
    for uid in nib.array(nib.top["UINibConnectionsKey"]):
        conn = nib.get(uid)
        if nib.class_name(conn) == "UIRuntimeOutletConnection":
            names[conn["UIDestination"].data] = str(nib.get(conn["UILabel"]))
    return names


def extract(nib: Nib) -> list[dict]:
    outlets = outlet_names(nib)
    elements: list[dict] = []

    def walk(uid, origin: tuple[float, float], depth: int) -> None:
        obj = nib.get(uid)
        if not isinstance(obj, dict) or obj.get("UIHidden"):
            return
        geometry = nib.geometry(obj)
        child_origin = origin
        if geometry is not None:
            cx, cy, width, height = geometry
            x, y = origin[0] + cx - width / 2, origin[1] + cy - height / 2
            if depth > 0:
                child_origin = (x, y)
            element = {"rect": [round(x, 1), round(y, 1), round(width, 1), round(height, 1)]}
            cls = nib.class_name(obj)
            if uid.data in outlets:
                element["outlet"] = outlets[uid.data]
            if cls in TEXT_CLASSES and obj.get("UIText") is not None:
                text = str(nib.get(obj["UIText"]))
                if text.strip():
                    element["text"] = text
            content = nib.button_content(obj)
            image = (content.get("background") or content.get("image")
                     or nib.image_name(obj.get("UIImage")))
            if content.get("image") and content.get("background"):
                element["foreground"] = content["image"]
            if image:
                element["image"] = image
            # Button titles were drawn in a clear colour; the visible words are labels.
            if "image" in element or "text" in element or "outlet" in element:
                elements.append(element)
        if "UISubviews" in obj:
            for child in nib.array(obj["UISubviews"]):
                walk(child, child_origin, depth + 1)

    for uid in nib.array(nib.top["UINibTopLevelObjectsKey"]):
        if nib.class_name(nib.get(uid)) != "UIProxyObject":
            walk(uid, (0.0, 0.0), 0)
    return elements


def main() -> None:
    for folder, code in LANGUAGE_FOLDERS.items():
        out = LAYOUTS_DIR / code
        out.mkdir(parents=True, exist_ok=True)
        count = 0
        for path in sorted((ORIGINAL_APP_DIR / folder).glob("*.nib")):
            elements = extract(Nib(path))
            (out / f"{path.stem}.json").write_text(
                json.dumps(elements, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            count += 1
        print(f"layouts/{code}: {count}")


if __name__ == "__main__":
    main()
