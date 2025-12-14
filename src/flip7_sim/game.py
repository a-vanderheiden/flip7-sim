
from enum import Enum
from typing import Any, Protocol, ClassVar
from random import sample, choice
from uuid import uuid4
import logging


######################################################################################################
# Cards
class CardType(Enum):
    NUMBER = "Number"
    MODIFIER = "Modifier"
    ACTION = "Action"

class Card(Protocol):
    """The each card class should contain the special code needed to evaluate the card.
    
    Ex. 
     - the number card should add itself to the player's hand
     - the draw three should make the player draw three cards,
     - the freeze card should change the players status to frozen 
    """
    title: str
    value: Any
    card_type: ClassVar[CardType]
    
    def resolve(self, **kwargs) -> None:
        """Defines how a card affects a player based on self.card_type"""
        ...

class NumberCard:

    card_type: CardType = CardType.NUMBER

    def __init__(self, title:str, value:int):
        self.title: str = title
        self.value: int = value

    def __str__(self) -> str:
        return f"[{self.title}]"
    
    def __gt__(self, other):
        """Used in sorting player hand"""
        return self.value > other.value

    def __eq__(self, other):
        """Determines membership in player.hand"""
        if not isinstance(other, NumberCard):
            return False
        else:
            return self.title == other.title

    def resolve(self, player, game, **kwargs) -> None:
        """Add number card to the player's hand"""

        # Check to see if player busted
        if self in player.hand:
            logging.debug(f"{player.name} drew duplicate card")

            if player.second_chance:
                logging.debug(f"{player.name} had a second chance; {self.title} discarded")
                game.discard.append(self)
                player.second_chance = False
            else:
                player.busted = True
                logging.info(f"{player.name} busted")

                game.discard.append(self)
                game.discard.extend(player.hand)
                game.discard.extend(player.modifier_hand)
                game.discard.extend(player.action_hand)

                player.hand = []
                player.modifier_hand = [] 
                player.action_hand = []
                player.active = False

        # Add card to player hand
        if not player.busted:
            player.hand.append(self)
            player.hand = sorted(player.hand)

class AddModifierCard:

    card_type: CardType = CardType.MODIFIER

    def __init__(self, title:str, value:int):
        self.title: str = title
        self.value: int = value

    def __str__(self) -> str:
        return f"[{self.title}]"
    
    def __gt__(self, other):
        return self.value > other.value
    
    def resolve(self, player, **kwargs) -> None:
        """Add modifier card to the players modifier_hand"""
        player.modifier_hand.append(self)
        player.modifier_hand = sorted(player.modifier_hand)

    def modify_score(self, score):
        """Mmodify the input score with the value of this card"""
        return score + self.value

class MultModifierCard:

    card_type: CardType = CardType.MODIFIER

    def __init__(self, title:str, value:int):
        self.title: str = title
        self.value: int = value

    def __str__(self) -> str:
        return f"[{self.title}]"
    
    def __gt__(self, other):
        return self.value > other.value
    
    def resolve(self, player, **kwargs) -> None:
        """Add modifier card to the players modifier_hand"""
        player.modifier_hand.append(self)
        player.modifier_hand = sorted(player.modifier_hand)
    
    def modify_score(self, score):
        """Mmodify the input score with the value of this card"""
        return score * self.value

class ActionCard:

    card_type: CardType = CardType.ACTION

    def __init__(self, title:str, value:int):
        self.title: str = title
        self.value: int = value

    def __str__(self) -> str:
        return f"[{self.title}]"
    
    def resolve(self, player, game) -> None:
        """
        Applies the Action to the player
        
        Action Cards:

            Draw 3 - player draws three cards
            Freeze - player is now inactive
            Second Chance - if a player draws a duplicate card, that card is discarded and the player does not bust
        """

        if self.title == "Draw3":
            player.draw()
            player.draw()
            player.draw()
        
        if self.title == "Freeze":
            player.active = False

        if self.title == "SecondChance":
            player.second_chance = True

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
            logging.info(f"{self.name} flipped 7 and gained 35 bonus points!")
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


class Flip7Game:
    def __init__(self):
        self.game_id: str = str(uuid4())
        self.players: list[Player] = make_players()
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
            logging.debug(f"Attempting to draw from the Deck (n={len(self.deck)})")
            drawn_card = self.deck.pop()
        except IndexError:
            logging.info(f"Deck empty, reshuffling Discard pile (n={len(self.discard)})")
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

    def who_to_draw_three(self, game:Flip7Game) -> Player:
        """Determines who the player will choose for the Draw 3"""
        ...

    def who_to_freeze(self, game:Flip7Game) -> Player:
        """Determines who the player will freeze"""
        ...

class ShayneToppStyle:
    """This style ALWAYS goes for it. More cards, more better"""

    style_code: str = "ST"

    def __init__(self, player_name) -> None:
        self.player_name = player_name

    def draw_again(self, game:Flip7Game) -> bool:
        """Always draw again"""
        return True
    
    def who_to_draw_three(self, game:Flip7Game) -> Player:
        """Always take the draw three"""

        return [player for player in game.players if player.name == self.player_name][0]

    def who_to_freeze(self, game:Flip7Game) -> Player:
        """Freeze the top threat to the player getting to draw again"""
        
        freeze_target = [player for player in game.players if player.name == self.player_name][0]

        other_players = [player for player in game.active_players if player.name != self.player_name]

        if other_players:
            freeze_target = sorted(other_players, key=lambda x: x.round_score)[-1]
        
        return freeze_target
    
class ThreeAndOutStyle(ShayneToppStyle):
    """This style stops taking more cards after they have any 3 number cards"""

    style_code: str = "3&O"

    def __init__(self, player_name) -> None:
        self.player_name = player_name

    def draw_again(self, game:Flip7Game) -> bool:
        """Do not draw after 3 number cards"""
        me = [player for player in game.players if player.name == self.player_name][0]

        return len(me.hand) < 3
    
    def who_to_draw_three(self, game:Flip7Game) -> Player:
        """Always take the draw three"""

        me = [player for player in game.players if player.name == self.player_name][0]

        draw3_target = me

        if len(me.hand) >= 3:
            draw3_target = choice(game.active_players)
        
        return draw3_target

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

    # TODO: Add action cards
    
    shuffled_deck = sample(deck, k=len(deck))

    return shuffled_deck

def make_players(num_players: int = 5, styles:list[PlayerStyle] = ALL_PLAYER_STYLES) -> list[Player]:
    """Create a list of players for the game."""

    player_list = []
    for i in range(1, num_players+1):
        name = f"Player {i}"
        style = styles[i % len(styles)]
        player = Player(name, style(name))
        player_list.append(player)
    
    return player_list
