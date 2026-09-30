"""Tutorial texts and order. The original's texts (Command tutorialText) described touches and
moving the phone, for example "Twist It: Swipe 2 fingers on the Twister in opposite
directions. Or quickly twist the iPhone for an X-Move Bonus!". Here each names the command
and its key, and Shout keeps its microphone X-Move (see docs/DEVIATIONS.md)."""

from bopit.input_map import key_name_for

# Help's Tutorials tab: a grid of four columns, read row by row.
TUTORIAL_ORDER = ("Bop", "Twist", "Pull", "Spin",
                  "Flick", "Shout", "Squeeze", "Crank",
                  "Shake", "Nail", "Brush", "Poke")

SHOUT_X_MOVE = " Or shout “Yeah!” into your microphone for an X-Move Bonus!"


def tutorial_text(command: str, microphone: bool = True) -> str:
    """Shown at the top of the tutorial and on the help popup during a game."""
    key = key_name_for(command) or "no key"
    text = f"{command} It: press {key}."
    if command == "Shout" and microphone:
        text += SHOUT_X_MOVE
    return text
