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

## Game engine

Source: the decompiled GameController, Command and mode classes, unless noted. Times are in seconds at normal speed (pitch 1.0). Every timer marked "per pitch" is divided by the current pitch, so the game speeds up by raising the pitch.

### Commands

- The master command list, in order (GameSettings::createCommands): Bop, Twist, Pull, Spin, Flick, Shout, Squeeze, Crank, Shake, Nail, Brush, Poke. Shout is left out entirely when the Shout It setting is off.
- Each command has a callout sound and a response sound. Callout: VO_<Name> in VOX mode, SFX_<Name>_C otherwise. Response: SFX_<Name>_R (Command_Bop::init shown; the others follow the same pattern, still to be checked one by one).
- In Silent mode the command sounds are not preloaded (GameSettings::preloadSounds), so no callout plays; the original showed the command as a picture (silentCallOutImage).
- Callouts and responses play at the SFX volume and at the current pitch.

### A game

1. The game waits on "Bop It to start": only Bop is active, and a touch starts the game (GameController::prepBopItToStart, gotOutOfTurnTouchEnded).
2. startGame: pitch 1.0, score 0, bonus 0, base bonus 100. The mode's active commands are set up. The first game music loop starts at the current pitch. The first command is chosen at random from the active commands and its callout plays immediately.
3. 0.81 per pitch later the first turn starts (startTurn).
4. A turn: input is accepted. A timeout is set for 1.1 per pitch. Beat animations run every 0.21 per pitch, up to 4 beats.
5. On a correct move (winTurn): the response sound plays at the current pitch, the music plays its "b" segment, score goes up by 1, bonus score goes up by the base bonus. The next command is chosen at random from the active commands and its callout plays right away. 0.81 per pitch later the next turn starts.
6. On a wrong move, or on timeout (commandTimeout), the turn fails. At timeout a command that registered a motion (X-Move) during the turn wins instead, except Bop, which can never be won by timeout.

### Wrong moves

- Wrong moves fail. Confirmed by the developer, and in the code: when a touch ends, the current command checks the finished gesture, and if it does not match, the turn fails at once (GameController::gotTouchEnded). When a touch begins, a gesture that does not match yet is simply waited on (gotTouchBegan), since it may still become the right move.
- A clearly wrong phone motion also fails the turn at once (forceLose, set in the X-Move commands' gotAccelerometer).
- The game has a hidden cheat flag (GameSettings amCheating) that makes every finished touch a win.
- A correct X-Move wins the turn, adds 25 to the end bonus and counts an X-Move.

### Shout It X-Move (microphone)

- During a Shout turn the original turned on the microphone (InputController startTurn:andNeedsMicrophone), starting only after the callout had played (startAudio is delayed by the callout length). A loud enough peak won the turn as an X-Move (GameController::gotAudio:peakPower), with the X-Move bonus of 25 and an X-Move count. The exact threshold is still to be read from Command_Shout.
- Planned for this port, agreed with the developer: the key still works as the plain move; during Shout turns the microphone is opened and only its level is measured; the input is never played back; a setting turns this on or off, defaulting to on.

### Speed

- Every 12 successful moves (pitchShiftFrequency), the pitch rises by the mode's pitch shift amount and the base bonus rises by 5 (GameController::successDone).
- Pitch shift amount: Classic 0.03, Basic 0.02, Extreme 0.02 (read from the machine code of each mode's startGame). Blitz never speeds up (frequency 50,000,000).
- Every 3rd speed up, the music moves to the next loop. With the Original theme the loops go 01, 02, 03, then back to 01.

### Music and the beat

- Game music is three loops, each an "a" part and a "b" part: MUSIC_GameLoop_01a and 01b, 02a and 02b, 03a and 03b, through the theme filter.
- The "a" parts are 2.437 seconds long, exactly 3 beats of 0.8125 seconds. The "b" parts are exactly 1 beat. The 0.81 second constants in the engine are one beat. (Measured from the files.)
- startGame starts the "a" loop looping at the current pitch, at volume 0, and then sets it to the music volume.
- The "a" loop is jumped to loopOffset, 1.62 seconds, which is the start of its third beat: once at game start and again on every success (playBeatForTurn). loopOffset is 1.66 on an iPhone 3G, presumably to cover that device's slower audio; this port uses 1.62. (GameController::init, read with the soft float decompile.)
- On every success the "b" part plays once on top, at the current pitch and music volume.
- So after each success the loop wraps back to its start exactly when the next turn opens, one beat later. A PERFECT move lands one beat after the turn opens.
- Pitch changes are applied to the playing loop at once (setPitchForSoundWithName).
- The music stops when the game fails or ends.

### Input between turns

- Input is only taken during a turn, from startTurn until the turn is won or failed (InputController inTurn). A touch between turns, for example during the callout, is ignored, except that on the "Bop It to start" screen it starts the game (gotOutOfTurnTouchEnded).

### Failing and game over

1. The music stops and a random death line plays (VO_Die_01 to 04).
2. If the failed command had been called 2 times or fewer in this game (Command::hasShownError, counted in Command::startTurn), the original showed a help popup for it: an animation and the command's how-to text, such as "Bop It: Tap on the Bop with 1 or 2 fingers" (GameViewController::displayError). The game then waited until the player pressed the popup's back button (errorBackPressed) before going on to step 3. Otherwise, 1 second later:
3. If Banter is on, a banter line plays.
4. 1 second later the game ends (failDone). Solo modes end on the first failure.

### Banter

- Pools (GameController::setUpBanterArray): general lines 01, 03, 04, 05, 09, 10, 11, 12, 13, 15, 16, 17, 18, 19, 24, 28, 30, 32, 36, 40, 41, 50, 57, 58. Low score lines 08, 14, 25, 27, 33, 35, 51, 52, 53, 55, 56. High score lines 02, 07, 20, 21, 26, 29, 31, 34, 37, 38, 39, 54, 59, 60. Lines 50 and up are only used when the device language is English.
- On a failure with a score under 50, a line is drawn from the general and low score pools together; at 50 or more, from the general and high score pools. Lines are not repeated until a pool is used up (playRandomBanter).

### Rhythm grading (Basic and Extreme only)

- Only Basic and Extreme grade timing (they call checkInputTiming; Classic and Blitz do not).
- The grade depends on the position of the game music in its "a" loop when the move is made. PERFECT: 0.78 to 0.84. GOOD: 0.75 to 0.78 or 0.84 to 0.87. OK: 0 to 0.75 or 0.87 to 1.91. Anything else is logged as "should have lost" but not punished.
- End bonus per move: PERFECT 75 (100 during a perfect streak, 85 during a good streak). GOOD 50 (75 during a perfect streak, 60 during a good streak). OK resets streaks and counts.
- Streaks after 25 graded moves: 25 perfects in a row starts a perfect streak (+100). Otherwise 25 perfects and goods start a good streak (+75). Details in GameController::postProcessInput.

### Modes

- Classic (SoloClassicMode): Bop, Twist and Pull. No unlocking. Speeds up 3 percent every 12 moves.
- Basic (SoloSingleObject) and Extreme (SoloMultipleMode) play the same way. The differences are visual (Basic shows one BopJect at a time full screen, Extreme shows them all), a first unlock count that is overwritten before it matters (12 and 8), and which call counts are set to 0 or 1, which affects the help popup. Both speed up 2 percent every 12 moves and are rhythm graded.
- Basic and Extreme, command by command (their winTurn, which runs before the base winTurn):
  - The game starts with only Bop active, and Bop is the first command.
  - On the 1st success, Bop is called again.
  - On the 2nd success, Twist is introduced (position 0).
  - On the 7th success, Pull is introduced (position 3), and 9 more successes are needed for the next unlock (the same win then counts one of them, so 8 more).
  - From then on, commands unlock in master list order after 8, then 9, 10, 11 more successes and so on (after the Nth regular unlock, the next needs N + 8). In practice Spin unlocks on success 15, Flick on 24, the next on 34, the next on 45.
- Screen positions decide which commands stay active (GameController::activateCommand:forLoc). There are 6 positions, 0 to 5. Activating a command at a position removes whatever command was there. Bop is always at position 4 and Poke always at 5; the others take the position given.
- A newly unlocked command goes to position 2 when 3 commands are active, 1 when 4 are active, 3 when 2 are active, otherwise 0. When 5 or more are active it replaces the second command in the active list (the oldest after Bop), except Poke, which takes position 5. So at most 6 are active at once.
- A newly unlocked or introduced command is called at once as the next command, and becomes active when that turn starts.
- Each unlock also raises the base bonus by 5.
- Once every command has been unlocked, each further unlock picks a random command from master list entries 1 to 10 that is not active (up to 6 tries, otherwise nothing changes), at a random position from 0 to 3.
- Command call counts (used for the help popup) are stored on the command objects, which live until the command list is rebuilt (theme change or Shout It change). A new game resets only the counts of the commands active at its start.
- Blitz (SoloSpeedMode):
  - Bop, Twist, Pull, Spin and Flick are all active from the start. Pitch stays at 1.0 (pitch shift frequency 50,000,000). Nothing unlocks. No rhythm grading.
  - Its music is MUSIC_BlitzLoop_01a and 01b (with theme variants), used the same way as the game loops.
  - A stopwatch starts with the game (startBlitzTimer). During play the original showed whole seconds (updateTime, format %i).
  - Mistakes do not end the game (SoloSpeedMode::failTurn). A wrong move or a timeout plays a random death line; the music keeps playing and jumps back to the loop offset, a new random command is called at once, and the next turn opens 0.81 seconds later. No help popup, no banter. So a mistake costs time.
  - On the 20th success the stopwatch stops. The normal success still plays and the next callout starts, then winBlitz cuts that callout off, stops the music and shows the end screen.
  - Times are kept per mode in a top 10 list, fastest first, with a 0 placeholder that counts as an empty slot (GameSettings::saveGameModeTime). A time slower than every entry in a full list is not kept.
  - The intro shows "High Score" and the best time as "%0.4f Seconds".
  - End screen (SoloBlitzEndGame): as the screen finishes sliding in (0.7 seconds), MUSIC_PayoffLoopShort plays at the music volume; 1 second later the time appears as "%.3fs", for example "23.037s"; if it beats the best time (or there was none), 0.5 seconds later SFX_HighScore.
- Unlocked commands come in master list order. Once all are unlocked, a random command is forced instead (GameController::unlockNextCommand).
- The very first game ever shows the tutorial popup instead of the mode intro (hasShownTutorialPopup).

### Command sound exceptions

- Crank uses SFX_Turn_C and SFX_Turn_R. Brush uses SFX_Pet_C and SFX_Pet_R. (Command_Crank::init, Command_Brush::init.)
- Only Shout's sound effects go through the theme filter. The death lines (VO_Die_01 to 04) also do. Banter does not. Of the game music, only the first loop (01a and 01b) has theme variants.

### Around a game

- Choosing a mode creates the game controller, which stops the menu music (GameController::init).
- The mode intro's Start plays SFX_Select, then the "Bop It to start" screen appears. The intro's Back plays nothing.
- The intro's Back and the end screen's Menu both return to the main menu, not the mode list, and restart the menu music (GameController::returnToMenu).
- The end screen's Play Again goes straight into a new game without the "Bop It to start" screen (SoloEndGame::playAgainButtonPressed calls prepBopItToStart then startGame). On screen, Play Again is just above Menu and Submit Score.

### Pause, saved game and Quick Play

- Pausing (GameController::pauseGame) does nothing once the player has failed. Otherwise it cancels the turn, activates any forced command, cuts off the queued callout (only if that command was not the last in the active list), stops the music and shows the pause menu. Blitz also stops its stopwatch.
- Pause menu, top to bottom: Resume, then Menu and Restart side by side, then the label "game progress saved". Each button plays SFX_Select.
- Resume (GameController::resumeGame): the game music restarts at the current pitch and jumps to the loop offset, a new random command (or the forced one) is called, and the turn opens 0.81 per pitch later. Blitz's stopwatch carries on from where it stopped.
- Menu (PauseMenu::exitButtonPressed): if at least one move was made, the game is saved to saveGame.dat; then back to the main menu.
- Restart: straight into a new game.
- The saved game keeps mode, moves, bonus, end bonus, unlock progress, pitch, active commands, Blitz time, X-Move count, rhythm counts, base bonus and music track (GameController::encodeWithCoder). It does not keep the speed up count within the current track or the streak state.
- Loading the saved game removes the file. Starting any new game also removes it ("Once you start any new game, your saved game is lost.").
- The main menu's Play button reads "Quick Play", or "Resume Game" while a saved game exists (LandingPage::setPlayButtonLabel). Pressed, it resumes the saved game, paused; otherwise it starts the Quick Play mode through its intro, which is Basic unless another mode was chosen (LandingPage::executePlayButtonPressed).
- At launch, a saved game is resumed straight away, paused (Bop_ItAppDelegate::doFinishLaunching).
- Choosing the Quick Play mode (SoloGameOptions classicButtonDown and friends): pressing a mode button starts a 1.2 second timer. If it fires while the button is still held, that mode becomes the Quick Play mode (saved as PlayButtonMode), SFX_SelectGame plays, and the button gets a "default selected" marker. On release, the mode starts only if the button was held 1.1 seconds or less. The help text says "2 seconds", but the code uses 1.2.
- The first time the Solo screen is ever opened, a popup says "press and hold any game mode button to make it your Quick Play game" with a close button (popupForDefaultButton). Closing it plays no sound.

### High scores

- Each mode keeps a top 10 list of entries with a score (the total) and moves, highest first. A new mode starts with one placeholder entry of 0 and 0. A new score is inserted above the first entry it ties or beats, and the list is cut to 10 (GameSettings::saveGameModeScore, getGameModeScore).
- "High Score" on the intro screen is the top entry's moves and points (getHighScore, getHighMove).
- The end screen plays SFX_HighScore when the total beats the previous top score.

### End screen (solo)

- Total score = moves + bonus score + end bonus (SoloEndGame::calcTotalScore). High scores are saved per mode as total score and moves.
- The end screen animates in (0.5 second delay plus UIKit's default 0.2 second animation) and then waits 0.5 seconds, so the scores appear about 1.2 seconds after the game ends.
- Sequence: SFX_BonusScore as Moves and Points (moves plus bonus score) appear. 1 second later, in Basic and Extreme, SFX_BonusScore again as Bonus (end bonus) appears, then 0.5 seconds later SFX_ScoreAnimation while Points counts up to the total, adding 5 percent of the difference (rounded up) every 1/60 second. If the total is 0 it plays SFX_BonusScore instead of counting. 1 second after the count finishes comes the feedback. Classic leaves Bonus blank and gives the feedback 2 seconds after the scores appear.
- Feedback: if the total beats the previous top score, SFX_HighScore. Otherwise a random gameplay tip is shown.

### Trophies and unlock messages

- The first time a command is ever unlocked, its "BopJect unlocked" trophy is completed and saved, and a message is shown, such as "Spin to Win! Spin Unlocked" (TrophyManager::unlockBopject; the messages are in Localizable.strings). It is only shown once.
- Other trophies, the gameplay tips and the Trophies screen are still to be read.

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
