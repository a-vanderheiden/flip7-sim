# flip7-sim
Simulation of the Flip 7 card game


## Install
1. Clone from github
```shell
git clone https://github.com/a-vanderheiden/flip7-sim
```
2. Create venv (optional)
```shell
python -m venv .venv/
source .venv/bin/activate # linux/macos
```
3. Install locally with `pip`
```shell
(.venv) pip install - e .
```

## Usage
Once installed, run with the `flip7` command. 
```shell
flip7
```
This kicks off a game of flip7 with 5 players by default. You can adjust the number of players with the `-n` flag

```shell
flip7 -n 8 # 8 player game
```

All player turns are recorded in a sqlite database (flip7-sim/db.sqlite) and written to a log file (flip7-sim/flip7-sim.log).

By default, the game is also shown visually by plotting the players' running scores overtime. The legend displays the player names as well as their play style.

You can save the plot interactively in the plot pop-up, automatically save it with `-s` (saves to `flip7-sim/plots/game_{game_id_abbrev}.png`), or suppress the figure all together with `--suppress-figure`.

```shell
flip7                   # interactive plt window
flip7 -s                # automatically save the figure to /plots
flip7 --suppress-figure # do not show or save figure
```
