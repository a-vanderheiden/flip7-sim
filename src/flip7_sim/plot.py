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

def get_round_locs_labels(df):
    """Get the x tick locations and labels for round starts"""
    round_ids = df.index.get_level_values("round_id")

    locs = []
    labels = []
    for i in round_ids.unique():
        locs.append(list(round_ids).index(i))
        labels.append(f"R{i}")

    return locs, labels

def get_player_styles(game_id:str, con:sqlite3.Connection) -> dict[str,str]:
    """Get the play style for each player in the game"""

    cursor = con.execute("SELECT player_id, profile FROM players WHERE game_id = :game_id", {"game_id":game_id})
    
    return dict(cursor.fetchall())

def make_summary_plot(game_id:str, con:sqlite3.Connection) -> None:
    df = get_turn_table(game_id, con)

    fig, ax = plt.subplots(1, 1, figsize=(8,4))

    df.plot(ax=ax, lw=1)

    # Title
    short_id = game_id.split("-")[0]
    ax.set_title(f"Score Summary (game {short_id})")

    # X axis
    ax.set_xlabel("Round")
    locs, labels = get_round_locs_labels(df)
    ax.set_xticks(locs)
    ax.set_xticklabels(labels)

    # Y axis
    ax.set_ylabel("Score")
    ax.axhline(200, ls="--", lw=0.5, c='r')

    # legend
    ax.legend(title="")
    # handles, labeles = ax.get_legend_handles_labels()
    player_styles = get_player_styles(game_id, con)
    ax.legend(labels= [f"{name} - {player_styles[name]}" for name in player_styles] )

    # Other
    ax.grid(axis="x")


def main():
    """Plots the flip7 game of a given ID"""

    con = sql_connect_to_db()

    game_id = get_last_game(con)

    make_summary_plot(game_id, con)

    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    short_id = game_id.split("-")[0]
    fig_path = PLOT_DIR / f"game_{short_id}.png"

    plt.savefig(fig_path, dpi=300)

if __name__ == "__main__":
    main()