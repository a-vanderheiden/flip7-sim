from argparse import ArgumentParser
import logging
logging.basicConfig(
    filename = "flip7-sim.log",
    encoding = "utf-8",
    filemode = "a",
    level = "DEBUG"
)

from flip7_sim import play_flip7

def main():

    parser = ArgumentParser(
        prog = "flip7",
        description = "Simulation of the Flip 7 card game",

    )

    parser.add_argument("-n", "--num-players", type=int, default=5)

    parser.add_argument("-p", "--print-logs", action="store_true")

    parser.add_argument("-f", "--figure", action="store_true")

    args = parser.parse_args()

    play_flip7(num_players=args.num_players)

    if args.figure:

        from flip7_sim.plot import main as plot_game
        plot_game()

if __name__ == "__main__":
    main()