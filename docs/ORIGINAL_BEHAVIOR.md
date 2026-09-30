# What we know about the original (Bop It for iOS, version 3.0)

Each fact notes how it was confirmed. Anything not listed here is unknown and must be asked about or recovered from the original app, never guessed.

## Sources

- `BopIt.app/English.lproj/Localizable.strings`: a binary plist with 178 English UI strings. Confirmed by decoding it with Python's plistlib.
- `BopIt.app/English.lproj/*.nib`: one compiled interface file per screen. Decoded with `tools/dump_nib.py` into plain text under `docs/original/nibs/`. Numbers shown in labels there, like scores, are designer placeholders, not real values.
- `BopIt.app/BopIt`: the ARM executable. Not analyzed yet.
- `BopIt.app/English Text.plist` and the other language plists hold only Origin social-network strings, and `help_text.txt` is EA's generic purchase FAQ. Neither describes gameplay.

## Screens

Source for this section: the decoded nibs. The original screens are touch layouts of round buttons scattered around the screen, not lists, so they have no inherent top-to-bottom order. Positions below are button centers in points on a 320 by 480 screen, x from the left and y from the top, listed top to bottom.

- Landing page (the main menu): Play (233, 206), Games (133, 240), Options (227, 312), More Games (144, 347). A tutorial button exists at (192, 448) but is hidden in the nib. A "swipe for themes" image sits at the bottom, and the background is a paging scroll view, which fits the Halloween and Christmas theme assets.
- Games page: Solo (135, 88), Multiplayer (85, 222), Trophies (244, 321), Scores (122, 356), Back (53, 433).
- Solo game options: Classic (118, 111), Basic (69, 219), Blitz (239, 297), Extreme (123, 327), Back (54, 434). Each mode button has separate "button down" and "pressed" actions. A hidden popup says "press and hold any game mode button to make it your Quick Play game", with a close button.
- Multiplayer options: Pass It Basic, Pass It Extreme, Head 2 Head, Blitz Challenge, Back, and the same Quick Play popup. Positions are relative to parent groups and not yet worked out.
- Options page: Help (221, 81), Settings (63, 122), Credits (251, 285), About (80, 320), Back (53, 432).
- Settings, top to bottom:
  - Commands: VOX, SFX or Silent, as three buttons.
  - Banter: On or Off.
  - Shout It: On or Off.
  - Music: a slider.
  - SFX: a slider.
  - Back.
- Game mode intro, shown before a game: mode name, mode description, "High Score" with best moves and best points, a START button, and Back.
- Pause menu: title "Paused", Resume, Menu (exits the game), Restart, and the label "game progress saved".
- Solo end game: Moves, Bonus and Points values, a gameplay tip label, Play Again, Menu, Submit Score, and a hidden trophies button.
- Solo Blitz end game: Time (shown like "23.037s"), a gameplay tip label, Play Again, Menu, Submit Score, and a hidden trophies button.
- Not yet read: Help, About, Credits, Scores, Trophies, the multiplayer end screens, Blitz player select, the command picker, the tutorial popup, and the in-game view.

## Game modes

Source for all of these: Localizable.strings. Order on screen is not yet confirmed.

- Solo modes are grouped under "Solo Game Modes", multiplayer modes under "Multiplayer Game Modes".
- Mode names found: Classic, Basic, Extreme, Blitz, Quick Play, Pass It Basic, Pass It Extreme, Head 2 Head, Blitz Challenge.
- Classic: "The original game of Bop, Twist and Pull. Just do what it says to stay alive as it gets faster and faster."
- Basic: "The Rhythm Challenge! Get Rhythm Bonus points for completing moves on the beat - a PERFECT awards the most points. Use X-Moves for additional bonus points."
- Extreme: "With as many 6 BopJects on screen at once, even a Bop Master will think this is Extreme! Get Rhythm Bonus points for completing moves on the beat. Use X-Moves for additional bonus points."
- Blitz: "Complete 20 moves as fast as you can. Just do what it says...only faster!"
- Blitz Challenge: "Challenge your friends to a game of Blitz. Take turns to see who can handle the pressure and get the fastest time!"
- Pass It Basic and Pass It Extreme: play Basic or Extreme with friends, passing after each move, either co-operatively or last player standing.
- Head 2 Head: each player completes moves on their half of the screen, tapping their half of the Bop first on "Bop It" scores a point, an opponent's mistake also scores, first to 7 wins.

## Commands

Source: Localizable.strings, plus matching voice files `VO_<Name>.wav` in English.lproj.

- The 12 commands are Bop, Twist, Pull, Flick, Spin, Shake, Crank, Shout, Squeeze, Nail, Brush, Poke.
- Unlock messages exist for Shake, Flick, Squeeze, Nail, Crank, Spin, Brush, Shout, Poke, which suggests Bop, Twist and Pull are available from the start. Not yet confirmed.
- Flick, Pull, Shake, Shout, Spin and Twist have an X-Move, a bonus way to perform them with the device's motion or microphone.
- Pass It has a `VO_Pass.wav` voice line.

## Sounds

Source: file listing of BopIt.app. The game loads copies from `sounds/`, made by `tools/extract_sounds.py`, which sorts them into folders but keeps the original filenames. The folders are our own organization, not the original's. All are 16-bit PCM WAV, mostly 22050 Hz mono.

- Each command has a correct sound (`SFX_<Name>_C.wav`) and a wrong sound (`SFX_<Name>_R.wav`). There are also Pet and Turn sound pairs whose use is unknown.
- Voice lines: banter (`VO_Banter_NN.wav`) and death lines (`VO_Die_01` to `04`).
- Music: menu music, game loops, Blitz loops, Pass It loops, payoff loops.
- Halloween (HLWN) and Christmas (XMAS) variants of some sounds and music exist. When they were used is unknown.

## Settings

Source: Localizable.strings. Meaning not yet confirmed.

- Labels: SFX, VOX, Silent, each with an "(X)" variant, plus On and Off with "(X)" variants.
- A reset of local scores exists: "Are you sure you want to reset your local scores?"

## Scoring and display

Source: Localizable.strings. Context not yet confirmed.

- "Level: %i", "%@ Points", "%i Moves", "Got to %i!", "High Score".
- Blitz times are shown to 4 decimal places ("%0.4f Seconds") and shared to 3.
- X-Move counts are reported as "Did %i X-Moves".
