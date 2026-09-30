# Debug mode

Debug mode lets the game play itself so you can listen to it, and writes every game event to a plain text log. It is off unless you start the game with `--debug`.

## Starting it

- `python -m bopit --debug` starts the game with the bot on. Pick any mode from the menus as usual; once the game screen opens, the bot takes over.
- `python -m bopit --help` lists every option.
- The console says that debug mode is on and where the log file is.

## Options

- `--reaction SECONDS`: how long after the turn opens the bot presses, at normal speed. The default is 0.3. The turn opens when the callout's voice starts, and the window is 1.1 seconds. Like every game timer, the reaction is divided by the current speed (pitch), so it keeps its place in the window as the game speeds up. For example, `--reaction 1.09` presses right at the edge of the window.
- `--fail KIND`: how the bot fails on purpose. `none` (the default) never fails. `wrong` presses a different command. `late` presses 0.05 seconds after the turn has timed out. `miss` presses nothing.
- `--fail-every N`: the bot fails on every Nth turn; the default is 10. In Classic, Basic, Extreme and Pass It the first failure ends the game. In Blitz and Blitz Challenge it costs time. In Head 2 Head it gives the other player a point.
- `--seed N`: a fixed random seed for every game, so a run repeats exactly. Without it, each game picks a seed and writes it in the log, so any run can be repeated later.
- `--no-bot`: log only, and you play yourself.

## What the bot does

- It presses Bop 1.5 seconds after "Bop it to start".
- On a help popup it waits 4 seconds so you can hear it, then continues.
- On the Blitz Challenge break screen it waits 3 seconds, then presses Next.
- In Head 2 Head it presses as the command's owner, and on a Bop the two players take turns winning. A wrong move is the owner pressing another of their own keys.
- End screens, the pause menu and all other menus are left to you.
- All speech and sound are exactly as in normal play.

## The log

- The file is `logs/debug-<date>-<time>.txt`, with one event per line.
- Each line starts with the seconds since the log opened, to the millisecond. The times are the engine's exact times, not the frame times.
- It logs screens, the seed and bot settings, commands called, turns opening with their window, the bot's presses, responses with the expected command and the delta from the turn opening, timeouts, scores, speed ups, rhythm grades, unlocks, points, results, and every sound and music change.
- Example lines:
  - `1.500 game started, Classic`
  - `2.310 turn opened: Twist, window 1.100`
  - `2.610 bot: presses Twist (right)`
  - `2.610 response: Twist, expected Twist, correct, delta 0.300`
  - `2.610 score: moves 1, bonus 100`
