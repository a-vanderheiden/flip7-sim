from argparse import ArgumentParser
import logging
logging.basicConfig(
    filename = "flip7-sim.log",
    encoding = "utf-8",
    filemode = "a",
    level = "DEBUG"
)

from flip7_sim import play_flip7
from flip7_sim.plot import main as plot_game

def main():

    parser = ArgumentParser()

    parser.add_argument("-n", "--num-players")

    parser.add_argument("-p", "--print-logs", action="store_true")

    parser.add_argument("-f", "--figure", action="store_true")

    args = parser.parse_args()

    play_flip7(int(args.num_players) or 5)

    if args.figure:
        plot_game()

if __name__ == "__main__":
    main()