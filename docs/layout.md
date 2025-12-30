# Code Layout

## Entry Point
The code's main entry point is in src/flip7_sim/__main__.py. The CLI is defined in this file. Next to nothing else should be defined here

## Primary Game Loop
The core logic for the game is in the function `play_flip7()` [`in game.py`](src/flip7_sim/game.py).

This function contains the primary game loop which builds a list of active players in the game, loops through this list of players and has each draw and resolve the card that it draws.

Both the players and cards here are abstractions. The effects of the cards are implemented in [`cards.py`](src/flip7_sim/cards.py) and the decision making for each player are handled by their `PlayerStyle`.

## Cards
After a player draws a card, the `.resolve()` method is called on that card and it will handle all of the required logic to move on to the next players turn. 

A player's cards are kept in separate hands (lists) based on the CardType. NumberCards are stored in `Player.hand`, `ModifierCards` are kept in `Player.modifier_hand`, and `ActionCards` are kept in `Player.action_hand`

```python
class Player:
    self.hand: list[NumberCard]
    self.modifier_hand: list[ModifierCard]
    self.action_hand: list[ActionCard]
```

All number cards are implemented with the NumberCard class. `NumberCard.resolve()` contains a fair amount of game logic to handle busts, flip 7s, and second chances. 

Modifier cards are implemented in two classes: AddModifierCard and MultModifierCard. Both of which take an integer as input to define the value of the score modifier. 

The three action cards are all implemented as individual classes: `FreezeActionCard`, `SecondChanceActionCard`, `DrawThreeActionCard` (under development).


## Player Styles

Several actions in Flip7 require decision making from the player - such as resolving any of the action cards and deciding when to stop drawing new cards. All of the decision making for a player is contained in the players `PlayerStyle`. `PlayerStyle` is a protocol class with methods that determine how a player will act in a given situation. 
```python
class PlayerStyle(Protocol):
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
    def who_to_give_2chance(self, game:Flip7Game) -> Player | None:
        """Determines who will receive the second chance"""
        ...
```

A `PlayerStyle` should be thought of like a player's personailty. For example, a player with the `ShaneToppPlayerStyle` is a player that always goes for the Flip7. They are crazed with getting the most points **this** round and will try and stop anyone who they think is the most likely threat to them getting a Flip7. 
