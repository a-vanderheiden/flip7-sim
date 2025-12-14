import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from flip7_sim.db import sql_connect_to_db

PLOT_DIR = Path("plots")

def get_turn_table(game_id:str, con:sqlite3.Connection):

    df = pd.read_sql_query(f"SELECT * FROM player_turns WHERE game_id = '{game_id}'", con)

    score_df = df.set_index(['round_id', 'turn_id', 'player_id'])[['game_score', 'round_score']]
    score_df["running_score"] = score_df["game_score"] + score_df["round_score"]
    running_score_df = score_df['running_score'].unstack('player_id')

    return running_score_df

def get_last_game(con:sqlite3.Connection):

    cursor = con.execute("SELECT * FROM games")

    last_game = cursor.fetchall()[-1]
    game_id, _time_stamp = last_game
    
    return game_id

def plot_game(game_id:str, con:sqlite3.Connection) -> None:
    df = get_turn_table(game_id, con)

    fig, ax = plt.subplots(1, 1)

    df.plot(ax=ax)
    short_id = game_id.split("-")[0]
    ax.set_title(f"Game {short_id}")

def main():
    """Plots the flip7 game of a given ID"""

    con = sql_connect_to_db()

    if len(sys.argv) > 1:
        game_id = sys.argv[1]
    else:
        game_id = get_last_game(con)

    plot_game(game_id, con)

    PLOT_DIR.mkdir(parents=True)
    short_id = game_id.split("-")[0]
    fig_path = PLOT_DIR / f"game_{short_id}.png"

    plt.savefig(fig_path, dpi=100)

if __name__ == "__main__":
    main()