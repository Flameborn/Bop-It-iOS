# What we know about the original (Bop It for iOS, version 3.0)

Each fact notes how it was confirmed. Anything not listed here is unknown and must be asked about or recovered from the original app, never guessed.

## Version

Source: BopIt.app/Info.plist. The bundle is "Bop It!", identifier com.ea.bopit.inc, app version 1.1.9, minimum iOS version 3.0, portrait only, status bar hidden. So "iOS 3.0" refers to the iOS requirement; the game itself is version 1.1.9.

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
- Multiplayer options: Pass It Basic (74, 145), Blitz Challenge (254, 225), Pass It Extreme (66, 325), Head 2 Head (207, 343), Back (53, 434), and the same Quick Play popup. These are screen positions worked out from nested views; the dumps list them as "screen center".
- Options page: Help (221, 81), Settings (63, 122), Credits (251, 285), About (80, 320), Back (53, 432).
- Settings, top to bottom:
  - Commands: VOX, SFX or Silent, as three buttons.
  - Banter: On or Off.
  - Shout It: On or Off.
  - Music: a slider.
  - SFX: a slider.
  - Back.
- Game mode intro, shown before a game. Top to bottom: mode name (y 44), mode description (140), "High Score" (231), best moves (266), best points (295), then START (202, 393) beside Back (99, 394).
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

- Each command has two sounds. Confirmed by the developer, who played the original:
  - `SFX_<Name>_C.wav` is the command sound. With Commands set to SFX, it replaces the voice calling out the command, such as "Bop it". This matches the help text, "SFX = Sound Effect Commands".
  - `SFX_<Name>_R.wav` is the response sound. It plays when the player performs the action.
- Pet and Turn also have C and R pairs, but there is no Pet or Turn command, so their use is unknown.
- Voice lines: banter (`VO_Banter_NN.wav`) and death lines (`VO_Die_01` to `04`).
- Music: menu music, game loops, Blitz loops, Pass It loops, payoff loops.
- Halloween (HLWN) and Christmas (XMAS) variants of some sounds and music exist. When they were used is unknown.

## Settings

Source: the Help screen's overview text in Help.nib, unless noted.

- Commands: "VOX = Voice Commands, SFX = Sound Effect Commands, SILENT = Text Commands (no audio)".
- Banter: "You can turn off the heckles and words of encouragement...but why?"
- Shout It: "Tap Off to remove Shout It from all gameplay".
- Music and SFX: sliders to "Adjust the game's audio mix".
- Localizable.strings also has SFX, VOX, Silent, On and Off each with an "(X)" variant. The "(X)" marks the selected option (see Settings internals).
- Reset of local scores, from the Scores screen: "Are you sure you want to reset your local scores?" (Localizable.strings).

## Settings internals

Source: Ghidra decompile of the armv7 binary (tools/decompile.py), functions named below.

- Defaults on first launch, from GameSettings::loadGameSettings: Commands VOX, Banter on, Shout It on, vibrate off, SFX volume 0.6, music volume 1.0. The two volumes were read from the machine code, since the decompiler lost them: 0x3f19999a is 0.6 and 0x3f800000 is 1.0.
- Commands is stored as whichKindOfCommands: 0 VOX, 1 Silent, 2 SFX. That is not the on-screen order, which is VOX, SFX, Silent.
- "(X)" marks the selected option: choosing VOX retitles its button "VOX (X)".
- Choosing a Commands option (Settings::commandsBtnPressed):
  - VOX plays VO_Bop, then restarts the menu music.
  - SFX plays SFX_Bop_R, then restarts the menu music.
  - Silent stops the menu music.
- Banter and Shout It (Settings::banterBtnPressed, shoutItBtnPressed) play SFX_SettingsSelect.
- Moving the SFX slider (Settings::sfxValueChange) plays SFX_Bop_R at the new volume, except when Commands is Silent.
- Moving the Music slider (Settings::musicValueChange) changes the playing music's volume and plays nothing.
- A vibrate setting and a difficulty button handler exist in code but have no button in the English Settings nib.
- The only global mute (GameSettings::muteSound) happens when the app goes to the background, not for Silent.

## Menu sounds and music

Source: the decompiled button handlers, and confirmed by the developer from memory.

- Sounds play only when something is selected. There is no sound for moving between items, since it was a touch screen (developer).
- SFX_Select: Games, Options and More Games on the main menu; all Games page buttons; all Options page buttons; end-of-game buttons; pause menu buttons; the GO buttons of Blitz player select, the Blitz break screen and the command picker.
- SFX_SelectGame: Play on the main menu, and every solo and multiplayer mode button.
- SFX_Back: every Back button.
- SFX_SettingsSelect: Banter, Shout It, and command picker toggles. The command picker also uses SFX_BackButtonOLD, probably when a command is turned off; not yet confirmed.
- No sound: the Scores tabs, and the Help screen's Overview and Tutorials tabs.
- All volumes use the SFX volume.
- MUSIC_MenuMusic loops across every menu screen (developer). It starts at launch without checking the Commands setting (Bop_ItAppDelegate::doFinishLaunching). It stops when a game starts (GameController::init) and restarts on returning to the menu (GameController::returnToMenu, returnBack).
- At launch, if a saved game exists (saveGame.dat), the game resumes it instead of starting the menu music.

## Themes

Source: SkinsManager and LandingPage in the decompile.

- Three skins: Original (skinMode 0), Halloween (1), Christmas (2). The first launch uses Original. The choice is saved (kCurrentThemeUsed).
- The main menu is a horizontally paging view. Swiping to the next page goes Original, Halloween, Christmas, then back to Original.
- Changing skin stops and restarts the menu music (in the new skin), and rebuilds the command list (GameSettings::createCommands). How commands differ by skin is not yet known.
- SkinsManager::GetSkinFilename inserts "_HLWN" or "_XMAS" before ".wav". The original only routes some sounds through it: menu button sounds, menu music, and some in-game sounds. Settings previews do not go through it.

## Help screen overview text

Source: Help.nib. The full text is in `docs/original/nibs/Help.txt`. Facts it adds beyond the sections above:

- There are 4 solo modes and 4 multiplayer modes, and 12 moves.
- In every mode "the game will tell you what move to do, and you do it before the time runs out."
- Basic: "To complete moves on the beat, you can take a hint from the BopJects dancing up & down. Try to time your move with the end of the second down."
- Extreme has "as many as 6 BopJects on screen at once".
- Bonus points are awarded in Basic and Extreme only. Blitz is scored as a time rather than moves and points.
- Pause: "You can return to the game by pressing the Resume Game button in the main menu. Once you start any new game, your saved game is lost."
- Quick Play: "You can set which game is launched by the Quick Play button. Press and hold any game mode button for 2 seconds."
- The Help screen has two tabs, "overview" and "tutorials". Tutorials has one button per command, 12 in all.

## Other screens

Source: the decoded nibs.

- Tutorial popup: "Would you like to see the tutorials and try the moves before playing?" with yes and no, and "access tutorials any time in options>help". When it appears is unknown.
- Command picker, titled "customize game": one toggle per command, with Bop It marked "(X)" (probably always on), a GO button, Back, and the hint "Add 2-4 BopJects to Bop It". Which mode uses it is unknown.
- Scores: mode tabs Classic, Basic, Extreme, Blitz; WEEKLY and ALL TIME tabs; Local, Friends and Global tabs; columns Name, Moves, Points, or Name and Time for Blitz; Back and a reset button.
- Trophies: a list with Back. Locked and unlocked trophy cells exist. Badge images badge_1 to badge_10 exist.
- About: "© KID Group LLC 2011. All rights reserved.", a version number, a note that Bop It was created by the original inventor of the Hasbro game, the Hasbro trademark notice, and the EA customer service address and license notice.
- Credits: KID Group for concept and production, Riptide Games for software development, Hasbro and Adam Rossi Audio for audio, Perez Design for 3D assets, thanks to Hasbro and EA. The full names are in `docs/original/nibs/Credits.txt`.

## Scoring and display

Source: Localizable.strings. Context not yet confirmed.

- "Level: %i", "%@ Points", "%i Moves", "Got to %i!", "High Score".
- Blitz times are shown to 4 decimal places ("%0.4f Seconds") and shared to 3.
- X-Move counts are reported as "Did %i X-Moves".
