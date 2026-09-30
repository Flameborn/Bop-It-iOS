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

The original showed moves and points on screen during a game. Here a key (currently S) speaks them on demand instead of after every move, which would talk over the callouts. It never counts as a move. Reason: accessibility. Approved 2026-09-29.

## Tutorial popup left out for now

The original asked "Would you like to see the tutorials and try the moves before playing?" before the very first game. It is left out until tutorials are designed for this port. Approved 2026-09-29.

## Sliders move in 10 percent steps

The Music and SFX sliders were continuous touch sliders. With the keyboard, each press moves them 10 percent. Reason: keyboard operation. Approved 2026-09-29.
