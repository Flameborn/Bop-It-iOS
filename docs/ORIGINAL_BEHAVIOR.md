# What we know about the original (Bop It for iOS, version 3.0)

Each fact notes how it was confirmed. Anything not listed here is unknown and must be asked about or recovered from the original app, never guessed.

## Sources

- `BopIt.app/English.lproj/Localizable.strings`: a binary plist with 178 English UI strings. Confirmed by decoding it with Python's plistlib.
- `BopIt.app/English.lproj/*.nib`: one compiled interface file per screen. Not decoded yet.
- `BopIt.app/BopIt`: the ARM executable. Not analyzed yet.
- `BopIt.app/English Text.plist` and the other language plists hold only Origin social-network strings, and `help_text.txt` is EA's generic purchase FAQ. Neither describes gameplay.

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

Source: file listing of BopIt.app.

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
