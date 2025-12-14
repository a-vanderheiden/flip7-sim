
import logging
logging.basicConfig(
    filename = "flip7-sim.log",
    encoding = "utf-8",
    filemode = "a",
    level = "DEBUG"
)

from flip7_sim import Flip7Game
from flip7_sim.db import sql_connect_to_db, sql_write_game, sql_write_players, sql_write_player_turn


def main():
    """
    Simulate a game of Flip 7

    Terms:

    Game: composed of multiple Rounds 
    
    Round: each active player takes a Turn in order until there are no active players remaining. A player is 
        active if they either bust (have two of the same number cards) or decide to stay

    Turn: composed of a player drawing a card from the deck and adding it to their hand. If that card 
        is a number card that is already in the player's hand, that player busted
    """

    # DB_NAME = "db.db"
    # CON = sqlite3.connect(DB_NAME)
    # sql_register_sqlite_converters()
    # sql_create_db(CON)

    CON = sql_connect_to_db()

    GAME = Flip7Game()
    sql_write_game(GAME, CON)
    sql_write_players(GAME, CON)

    logging.info(f"--- BEGIN GAME {GAME.game_id} ---")

    # Start Game 
    while all([player.game_score < GAME.win_score for player in GAME.players]):

        # Start Round
        GAME.round_num += 1
        logging.info(f"--- STARTING ROUND {GAME.round_num} ---")
    
        GAME.active_players = [player for player in GAME.players if player.is_active()]

        while GAME.active_players:
            
            for player in GAME.active_players:

                # Start Turn
                player.turn += 1
                logging.info(f"{player.name} turn {player.turn}")

                if player.play_style.draw_again(GAME):
                    
                    drawn_card = GAME.draw_card()
                    logging.info(f"{player.name} drew a {drawn_card.title}")

                    # Resolve card based on type
                    drawn_card.resolve(player = player, game = GAME)
                else:
                    player.stay = True

                # Update round score 
                player.update_round_score()

                logging.info(f"{player.name} action hand: {player.hand_string(player.action_hand)}")
                logging.info(f"{player.name} modifier hand: {player.hand_string(player.modifier_hand)}")
                logging.info(f"{player.name} hand: {player.hand_string(player.hand)}")
                logging.debug(f"{player.name} round score is now {player.round_score}")
                
                # Write player score to db
                sql_write_player_turn(player, GAME, CON)

                # Stop round if player gets 7 cards
                if len(player.hand) == 7:
                    break
                    
                # TODO: player can choose to stay or remain active

            if any([len(player.hand) == 7 for player in GAME.active_players]):
                break
            else:
                GAME.active_players = [player for player in GAME.players if player.is_active()]

        logging.info(f"Round {GAME.round_num}: Complete")

        # Update player status for next round
        for player in GAME.players:

            player.update_game_score()
            player.round_reset(GAME)
            logging.info(f"{player.name} Summary: round {player.round_score:03d}   game {player.game_score:03d}   hand {[c.value for c in player.hand] or '[busted]'}")

    logging.info(f"--- GAME OVER ---")
    winner = sorted(GAME.players, key=lambda p: p.game_score)[-1]
    logging.info(f"{winner.name} won with {winner.game_score} points!")

    logging.info(f"Game Summary:")
    for player in GAME.players:
        logging.info(f"{player.name}: {player.game_score}")

if __name__ == "__main__":
    main()