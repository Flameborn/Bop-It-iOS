"""Dump compiled iOS nib files as plain line-based text.

Usage: python tools/dump_nib.py OUTPUT_DIR NIB [NIB ...]

Each view is one line with its depth, class, id, text, image, center point and flags,
followed by outlet and action connections. Coordinates are in 320 by 480 points.
"""

import plistlib
import sys
from pathlib import Path
from typing import Any

UID = plistlib.UID


class Nib:
    def __init__(self, path: Path) -> None:
        archive = plistlib.loads(path.read_bytes())
        self.objects: list[Any] = archive["$objects"]
        self.top: dict[str, UID] = archive["$top"]

    def get(self, value: Any) -> Any:
        return self.objects[value.data] if isinstance(value, UID) else value

    def class_name(self, obj: Any) -> str:
        if isinstance(obj, dict) and "$class" in obj:
            name = self.get(obj["$class"])["$classname"]
            if name == "UIClassSwapper":
                return str(self.get(obj["UIClassName"]))
            return name
        return type(obj).__name__

    def array(self, value: Any) -> list[Any]:
        obj = self.get(value)
        if isinstance(obj, dict) and "NS.objects" in obj:
            return obj["NS.objects"]
        return []

    def describe(self, uid: UID) -> str:
        obj = self.get(uid)
        parts = [f"{self.class_name(obj)} #{uid.data}"]
        if not isinstance(obj, dict):
            return parts[0]
        text = obj.get("UIText")
        if text is not None:
            parts.append(f'text "{self.get(text)}"')
        content = self.button_content(obj)
        if content.get("title"):
            parts.append(f'title "{content["title"]}"')
        image = content.get("image") or self.image_name(obj.get("UIImage"))
        if image:
            parts.append(f"image {image}")
        if content.get("background"):
            parts.append(f"background {content['background']}")
        if "UICenter" in obj:
            parts.append(f"center {self.get(obj['UICenter']).strip('{}')}")
        if "UIBounds" in obj:
            size = self.get(obj["UIBounds"]).strip("{}").split("}, {")[-1]
            parts.append(f"size {size}")
        if obj.get("UIHidden"):
            parts.append("HIDDEN")
        if obj.get("UIUserInteractionDisabled"):
            parts.append("not interactive")
        if "UITag" in obj:
            parts.append(f"tag {obj['UITag']}")
        return ", ".join(parts)

    def image_name(self, value: Any) -> str | None:
        if value is None:
            return None
        image = self.get(value)
        if isinstance(image, dict) and "UIResourceName" in image:
            return str(self.get(image["UIResourceName"]))
        return None

    def button_content(self, obj: dict[str, Any]) -> dict[str, str]:
        """Title and images for the normal state, falling back to any state."""
        states = self.get(obj.get("UIButtonStatefulContent"))
        if not isinstance(states, dict) or "NS.objects" not in states:
            return {}
        result: dict[str, str] = {}
        for key, value in zip(states["NS.keys"], states["NS.objects"]):
            content = self.get(value)
            state = self.get(key)
            if not isinstance(content, dict):
                continue
            title = content.get("UITitle")
            if title is not None and ("title" not in result or state == 0):
                result["title"] = str(self.get(title))
            image = self.image_name(content.get("UIImage"))
            if image and ("image" not in result or state == 0):
                result["image"] = image
            background = self.image_name(content.get("UIBackgroundImage"))
            if background and ("background" not in result or state == 0):
                result["background"] = background
        return result

    def walk(self, uid: UID, depth: int, lines: list[str]) -> None:
        lines.append(f"depth {depth}: {self.describe(uid)}")
        obj = self.get(uid)
        if isinstance(obj, dict) and "UISubviews" in obj:
            for child in self.array(obj["UISubviews"]):
                self.walk(child, depth + 1, lines)

    def dump(self) -> list[str]:
        lines = ["Views:"]
        for uid in self.array(self.top["UINibTopLevelObjectsKey"]):
            obj = self.get(uid)
            if self.class_name(obj) == "UIProxyObject":
                continue
            self.walk(uid, 0, lines)
        lines.append("Connections:")
        for uid in self.array(self.top["UINibConnectionsKey"]):
            conn = self.get(uid)
            kind = self.class_name(conn)
            label = self.get(conn["UILabel"])
            source = self.describe(conn["UISource"])
            destination = self.describe(conn["UIDestination"])
            if kind == "UIRuntimeEventConnection":
                lines.append(f"action {label} sent by {source}")
            else:
                lines.append(f"outlet {label} is {destination}")
        return lines


def main() -> None:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[2:]:
        path = Path(arg)
        lines = [f"Nib: {path.name}"] + Nib(path).dump()
        (out_dir / f"{path.stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{path.name}: {len(lines)} lines")


if __name__ == "__main__":
    main()
