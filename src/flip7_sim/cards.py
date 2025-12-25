from enum import Enum
from typing import Protocol, Any, ClassVar
import logging



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

class FreezeActionCard:

    card_type: CardType = CardType.ACTION
    title: str = "freeze"
    value: str = "freeze"

    def __str__(self) -> str:
        return f"[{self.title}]"
    
    def resolve(self, player, game) -> None:
        """
        Applies the frozen status to a selected player. 

        `player` here decides who to apply the freeze to based on their play style.
        """

        target = player.who_to_freeze()

        target.frozen = True