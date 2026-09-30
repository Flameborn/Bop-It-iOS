# Deliberate deviations from the original

Each entry needs a reason and the developer's approval.

## Menu order is top to bottom

The original menus are touch screens with round buttons scattered around, so they have no list order. Menu items are listed by their on-screen position, top to bottom, using the button centers from the decoded nibs. Back is not a list item; it is on the back key. Reason: menus must be linear to be navigated by keyboard and speech. Approved 2026-09-29.

## Online features are left out

More Games (an EA store link), the Friends and Global score tabs, Weekly scores, Submit Score, Facebook sharing, and the Origin network are not included. Only local scores remain. Reason: the services behind them no longer exist. Approved 2026-09-29.

## Menus wrap around

Moving past the last item goes to the first, and the other way round. Reason: keyboard navigation convenience. Approved 2026-09-29.

## Theme is a menu item

The original changed skins (Original, Halloween, Christmas) by swiping the main menu sideways. Here it is a Theme choice at the bottom of the main menu, where the original's "swipe for themes" hint sat, changed with Left, Right or Enter. It cycles in the original's order and restarts the menu music like a swipe did. Reason: keyboard operation. Approved 2026-09-29.

## Escape on the main menu quits

The iPhone game had no way to quit. Here the back key on the main menu exits the game immediately, with no confirmation. Reason: a desktop program needs a keyboard way to exit. Approved 2026-09-29.

## Silent commands are not offered for now

The original's Commands setting had VOX, SFX and Silent. Silent showed each command as a picture with no sound, which cannot be played without sight. The Commands choice offers only VOX and SFX. The original's Silent behavior stays documented in ORIGINAL_BEHAVIOR.md and in code comments, in case it is added later. Reason: accessibility. Approved 2026-09-29.

## Help pause speaks the command's key

When a command called 2 times or fewer is failed, the original paused on a help popup with touch screen instructions until its back button was pressed. Here the pause speaks the command and its key, for example "Twist it. Key: left. Press Enter to continue.", and waits for Enter. The timing of the pause is unchanged. Reason: the touch instructions do not apply to a keyboard. Approved 2026-09-29.

## A key speaks the score during play

The original showed moves and points on screen during a game. Here a key (currently S) speaks them on demand instead of after every move, which would talk over the callouts. It never counts as a move. Points are moves plus bonus score, as the original showed them during play. Reason: accessibility. Approved 2026-09-29.

## Rhythm grades are spoken on request

In Basic and Extreme the original showed PERFECT, GOOD or OK after every move. Here the score key also says the last move's grade, for example "Last move Perfect." Speaking each grade automatically would land on top of the next callout. A later option could speak grades automatically, interrupting other speech. Reason: accessibility. Approved 2026-09-29.

## Streak banners are spoken

The original showed a "25 PERFECT streak" or "25 GOOD streak" banner. Here it is spoken, for example "25 Perfect streak." Reason: accessibility. Approved 2026-09-29.

## New commands are announced

In Basic and Extreme a new BopJect appeared on screen when a command entered play. Here its entrance is spoken, for example "Spin added." The first time a command is ever unlocked, the original's unlock message is spoken instead, for example "Spin to Win! Spin Unlocked", and remembered in progress.json so it is only heard once, as in the original. Reason: accessibility. Approved 2026-09-29.

## Tutorial popup left out for now

The original asked "Would you like to see the tutorials and try the moves before playing?" before the very first game. It is left out until tutorials are designed for this port. Approved 2026-09-29.

## Microphone setting for the Shout It X-Move

The original always used the microphone for the Shout It X-Move. It is kept here with the original's timing (listening starts 0.46 seconds per pitch into a Shout turn), threshold (0.6 linear average level) and bonus (25), but only the level is measured and nothing is played back. A Microphone setting, added as the last Settings item, turns it on or off; it defaults to on. If no microphone can be opened, "No microphone found. Use the Shout key." is spoken once and the key still works. Reason: desktop speakers can leak game sound into a microphone, which the phone's hardware did not. Approved 2026-09-29.

## Pause key and the back key in the pause menu

The original paused with an on-screen pause button. Here the back key (Escape) pauses during a game. In the pause menu the back key resumes, as pressing the original's pause button again closed the menu. On the "Bop It to start" screen, where there is nothing to pause yet, the back key returns to the main menu. Reason: keyboard operation. Approved 2026-09-29.

## Quick Play is chosen by holding Enter

The original chose the Quick Play mode by holding a mode button. Here Enter (or Space) is held on a mode, with the original's timings: 1.2 seconds sets it, a release within 1.1 seconds starts the mode. The original's "default selected" marker is spoken as the item's state ("Classic, Quick Play, 1 of 4") and the change is announced ("Classic is now your Quick Play game."). The first-visit popup reads "Press and hold Enter on any game mode to make it your Quick Play game" instead of "press and hold any game mode button". Reason: keyboard operation and accessibility. Approved 2026-09-29.

## Scores page adaptations

Only the local list is kept (the Friends, Global, Weekly and All Time tabs were online). The mode tabs are a Mode choice at the top. An empty list reads "No scores" rather than being silent. Reason: online services are gone; an empty table must be spoken. Approved 2026-09-29 as part of dropping online features.

## Trophy notices are spoken

The original's "new trophy" image during play, and the trophy shown on the end screen, are spoken as "New trophy." The end screen's trophy button becomes a "Trophies" item at the top of its menu. On the Trophies page, earned trophies read their medal ("bronze trophy") and the rest read "locked". Reason: accessibility. Approved 2026-09-29.

## Tips adapted for this port

Of the original's 12 end-screen tips: the two about Submit Score (Facebook and the leaderboard) are removed; three touch-screen and phone tips are rewritten: "Try holding the device flat, like it's on a table" became "Trouble with X-Moves? Shout it loud and close to your microphone", "Try Silent Mode" became "Turn the Microphone off in Options>Settings", and "Try doing the finger gesture directly on top of it" became "Wait for the command to finish, then press its key". The Tutorials tip is left out until tutorials exist. The rest, including the two Bop It XT and Bop It HD tips, are verbatim. The original's 26 percent chance and no-repeat order are kept. Reason: the originals referred to things this port does not have. Approved 2026-09-29.

## Help overview adapted for this port

The Help overview keeps the original's sections, order and wording except where it described the phone, the touch screen or online features (the port's text is in bopit/port_texts.py, the original in bopit/texts.py): the Zoom set-up note became a headphones note; "using the touch screen" became "using the keyboard"; the X-Move section describes the microphone shout; Basic's hint about the dancing BopJects became "listen to the music: time your move with the second beat after the command"; the Scoring section points to Games>Scores instead of the leaderboard and Facebook; the Facebook section is removed; the pause button became Escape; Silent is removed from the Commands line, "Tap Off" became "Set it to Off" and a Microphone line is added; Quick Play says "Press and hold Enter on any game mode for about a second" (the original said 2 seconds; its code used 1.2). The multiplayer descriptions are unchanged until multiplayer is built. Reason: the original text described things this port does not have. Approved 2026-09-30.

## Sliders move in 10 percent steps

The Music and SFX sliders were continuous touch sliders. With the keyboard, each press moves them 10 percent. Reason: keyboard operation. Approved 2026-09-29.
