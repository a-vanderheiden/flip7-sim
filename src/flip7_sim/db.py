from datetime import datetime
import sqlite3

from flip7_sim import Flip7Game, Player

DB_PATH = "db.sqlite3"

def sql_register_sqlite_converters() -> None:
    """
    Register sqlite converters to convert between python and sqlite
    
    See link below for discussion on type support between sqlite3 and python 3.12+
    https://docs.python.org/3/library/sqlite3.html#how-to-adapt-custom-python-types-to-sqlite-values

    Example sqlite adaptors and converters: https://docs.python.org/3/library/sqlite3.html#adapter-and-converter-recipes
    """
    import datetime
    import sqlite3

    def adapt_date_iso(val):
        """Adapt datetime.date to ISO 8601 date."""
        return val.isoformat()

    def adapt_datetime_iso(val):
        """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
        return val.replace(tzinfo=None).isoformat()

    def adapt_datetime_epoch(val):
        """Adapt datetime.datetime to Unix timestamp."""
        return int(val.timestamp())

    sqlite3.register_adapter(datetime.date, adapt_date_iso)
    sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
    # sqlite3.register_adapter(datetime.datetime, adapt_datetime_epoch)

    def convert_date(val):
        """Convert ISO 8601 date to datetime.date object."""
        return datetime.date.fromisoformat(val.decode())

    def convert_datetime(val):
        """Convert ISO 8601 datetime to datetime.datetime object."""
        return datetime.datetime.fromisoformat(val.decode())

    def convert_timestamp(val):
        """Convert Unix epoch timestamp to datetime.datetime object."""
        return datetime.datetime.fromtimestamp(int(val))

    sqlite3.register_converter("date", convert_date)
    sqlite3.register_converter("datetime", convert_datetime)
    sqlite3.register_converter("timestamp", convert_timestamp)

def sql_create_tables(con: sqlite3.Connection) -> None:
    """Create sqlite db to store game info"""

    cursor = con.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS games (game_id, timestamp)")
    cursor.execute("CREATE TABLE IF NOT EXISTS players (player_id, game_id, profile)")
    cursor.execute("CREATE TABLE IF NOT EXISTS player_turns (player_id, turn_id, round_id, game_id, game_score, round_score, num_cards, hand, stay, busted, frozen, second_chance)")


def sql_connect_to_db(db_path:str = DB_PATH) -> sqlite3.Connection: 
    """Initialize and connect to the sqlite database"""

    con = sqlite3.connect(DB_PATH)
    sql_register_sqlite_converters()
    sql_create_tables(con)

    return con


def sql_write_game(game:Flip7Game, con: sqlite3.Connection) -> None:
    """Log the game object"""

    cursor = con.cursor()

    cursor.execute("INSERT INTO games VALUES (?, ?)", (game.game_id, datetime.now()))
    con.commit()

def sql_write_players(game:Flip7Game, con: sqlite3.Connection) -> None:
    """Write players to the database"""
    cursor = con.cursor()
    for player in game.players:
        cursor.execute("INSERT INTO players VALUES (?, ?, ?)", (player.name, game.game_id, player.play_style.style_code))
    con.commit()

def sql_write_player_turn(player:Player, game:Flip7Game, con: sqlite3.Connection) -> None:
    cursor = con.cursor()

    data = {
        "player_id": player.name,
        "turn_id": player.turn,
        "round_id": game.round_num,
        "game_id": game.game_id,
        "game_score": player.game_score,
        "round_score": player.round_score,
        "num_cards": len(player.hand),
        "hand": str(player.dump_hand()),
        "stay": player.stay,
        "busted": player.busted,
        "frozen": player.frozen,
        "second_chance": player.second_chance
    }

    cursor.execute(
        "INSERT INTO player_turns VALUES (:player_id, :turn_id, :round_id, :game_id, :game_score, :round_score, :num_cards, :hand, :stay, :busted, :frozen, :second_chance)",
        data
    )
    con.commit()

