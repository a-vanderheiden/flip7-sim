from typing import Any, Protocol
from random import sample, choice
from uuid import uuid4
import logging

from .cards import Card, NumberCard, MultModifierCard, AddModifierCard, FreezeActionCard, SecondChanceActionCard, Flip3ActionCard
from .db import sql_connect_to_db, sql_write_game, sql_write_players, sql_write_player_turn

######################################################################################################
# Player and Game
class Player:

    def __init__(self, name: str, play_style: Any):
        self.name: str = name
        self.play_style: Any = play_style
        self.turn: int = 0
        self.round_score: int = 0
        self.game_score: int = 0
        self.hand: list = []
        self.modifier_hand: list = []
        self.action_hand: list = []
        self.busted: bool = False
        self.stay: bool = False
        self.frozen: bool = False
        self.second_chance: bool = False

    def is_active(self):
        """Determine if a player is active based on other statuses"""
        return not any([self.busted, self.stay, self.frozen])

    def update_round_score(self) -> None:
        """Update the player's score for the round based on number and modifier cards"""

        score = sum(c.value for c in self.hand)

        if len(self.hand) == 7:
            logging.debug(f"{self.name} flipped 7 and gained 35 bonus points!")
            score += 35 # should get this from game object?

        for card in self.modifier_hand:
            score = card.modify_score(score)
        
        self.round_score = score
    
    def update_game_score(self) -> None:
        self.game_score += self.round_score

    def hand_string(self, hand) -> str:
        return f"[{', '.join([str(card) for card in hand])}]"
    
    def round_reset(self, game):
        """Discard all cards and reset all statuses after a round finishes"""
        
        game.discard.extend(self.hand)
        self.hand = []
        game.discard.extend(self.modifier_hand)
        self.modifier_hand = []
        game.discard.extend(self.action_hand)
        self.action_hand = []

        self.busted = False
        self.stay = False
        self.second_chance = False
        self.frozen = False

        self.turn = 0
        self.round_score = 0
    
    def dump_hand(self) -> dict:
        """Return a dictionary representation of a players cards"""

        all_cards = {
            "number_cards": [str(c) for c in self.hand],
            "modifier_cards": [str(c) for c in self.modifier_hand],
            "action_cards": [str(c) for c in self.action_hand]
        }
        return all_cards
    
    def draw_again(self, game) -> bool:
        """Use self.play_style to determine if the player draws again"""
        return self.play_style.draw_again(game)
    
    def who_to_freeze(self, game):
        """Use self.play_style to determine who to freeze"""
        return self.play_style.who_to_freeze(game)
    
    def who_to_flip_three(self, game):
        """Use self.play_style to determine who make flip three cards"""
        return self.play_style.who_to_flip_three(game)
    
    def who_to_give_2chance(self, game):
        """Use self.player to determine who will receive the second chance card"""
        return self.play_style.who_to_give_2chance(game)



class Flip7Game:
    def __init__(self, num_players:int):
        self.game_id: str = str(uuid4())
        self.players: list[Player] = make_players(num_players)
        self.active_players: list[Player] = []
        self.deck: list[Card] = build_deck()
        self.discard: list[Card] = []
        self.win_score: int = 200
        self.flip7_bonus: int = 35
        self.round_num = 0

        pass
    
    def draw_card(self):
        """
        A card is drawn from the deck. If the deck runs out, the discard is reshuffled and replaces the deck
        """

        try:
            logging.debug(f" - GAME {self.game_id.split("-")[0]} - ROUND {self.round_num}: Attempting to draw from the Deck (n={len(self.deck)})")
            drawn_card = self.deck.pop()
        except IndexError:
            logging.info(f" - GAME {self.game_id.split("-")[0]} - ROUND {self.round_num}: Deck empty, reshuffling Discard pile (n={len(self.discard)})")
            self.deck = sample(self.discard, k=len(self.discard))
            self.discard = []
            drawn_card = self.deck.pop()
        
        return drawn_card


######################################################################################################
# Player Styles

class PlayerStyle(Protocol):
    """
    PlayerProfiles control how the player will respond to different scenarios in the game
    
    For example, the profile will determine when a player decides to stay vs take another card.
    """

    player_name: str
    style_code: str = ""

    def __call__(self, player_name):
        self.player_name = player_name

    def draw_again(self, game:Flip7Game) -> bool:
        """Determines if the player will draw again"""
        ...

    def who_to_flip_three(self, game:Flip7Game) -> Player:
        """Determines who the player will choose for the Flip 3"""
        ...

    def who_to_freeze(self, game:Flip7Game) -> Player:
        """Determines who the player will freeze"""
        ...

    def who_to_give_2chance(self, game:Flip7Game) -> Player | None:
        """Determines who will receive the second chance"""
        ...

class ShayneToppStyle:
    """This style ALWAYS goes for it. More cards, more better"""

    style_code: str = "ST"

    def __init__(self, player_name) -> None:
        self.player_name = player_name

    def draw_again(self, game:Flip7Game) -> bool:
        """Always draw again"""
        return True
    
    def who_to_flip_three(self, game:Flip7Game) -> Player:
        """Always take the flip three"""
        return [player for player in game.active_players if player.name == self.player_name][0]

    def who_to_freeze(self, game:Flip7Game) -> Player:
        """Freeze the top threat to the player getting to draw again"""
        
        freeze_target = [player for player in game.players if player.name == self.player_name][0]

        other_players = [player for player in game.active_players if player.name != self.player_name]

        if other_players:
            freeze_target = sorted(other_players, key=lambda x: x.round_score)[-1]
        
        return freeze_target
    
    def who_to_give_2chance(self, game:Flip7Game) -> Player | None:
        """Give the second chance to yourself, then a random other player, then discard"""

        me = [player for player in game.players if player.name == self.player_name][0]
        players_wo_2chance = [player for player in game.active_players if not player.second_chance]

        if me in players_wo_2chance:
            return me
        if players_wo_2chance:
            return choice(players_wo_2chance)
        else:
            return None
    
class ThreeAndOutStyle():
    """This style stops taking more cards after they have any 3 number cards"""

    style_code: str = "3&O"

    def __init__(self, player_name) -> None:
        self.player_name = player_name

    def draw_again(self, game:Flip7Game) -> bool:
        """Do not draw after 3 number cards"""
        me = [player for player in game.players if player.name == self.player_name][0]

        return len(me.hand) < 3
    
    def who_to_flip_three(self, game:Flip7Game) -> Player:
        """Take the flip three if you have no cards. Otherwise, choose another player at random"""

        me = [player for player in game.players if player.name == self.player_name][0]

        other_players = [player for player in game.active_players if player.name != self.player_name]

        if len(me.hand) == 0:
            return me
        elif other_players:
            return choice(other_players)
        else:
            return me
        
    def who_to_freeze(self, game:Flip7Game) -> Player:
        """Freeze the top threat to the player getting to draw again"""
        
        freeze_target = [player for player in game.players if player.name == self.player_name][0]

        other_players = [player for player in game.active_players if player.name != self.player_name]

        if other_players:
            freeze_target = sorted(other_players, key=lambda x: x.round_score)[-1]
        
        return freeze_target
    
    def who_to_give_2chance(self, game:Flip7Game) -> Player | None:
        """Give the second chance to yourself, then a random other player, then discard"""

        me = [player for player in game.players if player.name == self.player_name][0]
        players_wo_2chance = [player for player in game.active_players if not player.second_chance]

        if me in players_wo_2chance:
            return me
        if players_wo_2chance:
            return choice(players_wo_2chance)
        else:
            return None



ALL_PLAYER_STYLES = [ShayneToppStyle, ThreeAndOutStyle]

######################################################################################################
# Game building funcs

def build_deck() -> list[Card]:
    """Build the flip7 deck"""

    deck = []

    # Add number cards
    deck.append(NumberCard("0", 0))

    for i in range(1, 13):
        for j in range(i):
            deck.append(NumberCard(str(i), int(i)))

    # Add modifier cards
    deck.append(MultModifierCard("x2", 2))

    add_modifier_values = [2, 4, 6, 8, 10]
    for val in add_modifier_values:
        deck.append(AddModifierCard(f"+{val}", val))

    # Add action cards
    for i in range(3):
        deck.append(FreezeActionCard())
        deck.append(SecondChanceActionCard())
        deck.append(Flip3ActionCard())
    
    shuffled_deck = sample(deck, k=len(deck))

    return shuffled_deck

def make_players(num_players: int, styles:list[PlayerStyle] = ALL_PLAYER_STYLES) -> list[Player]:
    """Create a list of players for the game."""

    player_list = []
    for i in range(1, num_players+1):
        name = f"Player {i}"
        style = styles[i % len(styles)]
        player = Player(name, style(name))
        player_list.append(player)
    
    return player_list

def play_flip7(num_players:int = 5):
    """
    Simulate a game of Flip 7

    Terms:

    Game: composed of multiple Rounds 
    
    Round: each active player takes a Turn in order until there are no active players remaining. A player is 
        active if they either bust (have two of the same number cards) or decide to stay

    Turn: composed of a player drawing a card from the deck and adding it to their hand. If that card 
        is a number card that is already in the player's hand, that player busted
    """

    CON = sql_connect_to_db()

    GAME = Flip7Game(num_players)
    sql_write_game(GAME, CON)
    sql_write_players(GAME, CON)

    logging.info(f" - GAME {GAME.game_id.split("-")[0]}: BEGIN GAME ")

    # Start Game 
    while all([player.game_score < GAME.win_score for player in GAME.players]):

        # Start Round
        GAME.round_num += 1
        logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num}: STARTING ROUND")
    
        GAME.active_players = [player for player in GAME.players if player.is_active()]

        while GAME.active_players:
            
            for player in GAME.active_players:

                # Start Turn
                player.turn += 1
                logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num} - PLAYER {player.name}: turn {player.turn} start")

                if player.draw_again(GAME):
                    
                    drawn_card = GAME.draw_card()
                    logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num} - PLAYER {player.name}: drew a {drawn_card.title}")

                    # Resolve card based on type
                    drawn_card.resolve(player = player, game = GAME)
                else:
                    player.stay = True

                # Update round score 
                player.update_round_score()

                logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num} - PLAYER {player.name}: hand A: {player.hand_string(player.action_hand)} M: {player.hand_string(player.modifier_hand)} N: {player.hand_string(player.hand)}")
                logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num} - PLAYER {player.name}: round score is now {player.round_score}")
                
                # Write player score to db
                sql_write_player_turn(player, GAME, CON)

                # Stop round if player gets 7 cards
                if len(player.hand) == 7:
                    break

                # Stop rounds if player's potential game score exceeds 200
                if player.game_score + player.round_score > GAME.win_score:
                    break

            # Assess if current round needs more turns; if not, break else, rebuild active player list
            if any([len(player.hand) == 7 for player in GAME.active_players]):
                break
            elif any([p.game_score + p.round_score >= GAME.win_score for p in GAME.active_players]):
                break
            else:
                GAME.active_players = [player for player in GAME.players if player.is_active()]

        logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num}: Round Complete")

        # Update player status for next round
        for player in GAME.players:

            player.update_game_score()
            logging.info(f" - GAME {GAME.game_id.split("-")[0]} - ROUND {GAME.round_num} - PLAYER {player.name}: Score Summary: round {player.round_score:03d}   game {player.game_score:03d}   hand {[c.value for c in player.hand] or '[busted]'}")
            player.round_reset(GAME)

    logging.info(f" - GAME {GAME.game_id.split("-")[0]}: GAME OVER")
    winner = sorted(GAME.players, key=lambda p: p.game_score)[-1]
    logging.info(f" - GAME {GAME.game_id.split("-")[0]}: {winner.name} won with {winner.game_score} points!")

    logging.info(f" - GAME {GAME.game_id.split("-")[0]}: Game Summary:")
    for player in GAME.players:
        logging.info(f" - GAME {GAME.game_id.split("-")[0]}: {player.name}: {player.game_score}")