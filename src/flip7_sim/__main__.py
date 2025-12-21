from argparse import ArgumentParser
import logging
logging.basicConfig(
    filename = "flip7-sim.log",
    encoding = "utf-8",
    filemode = "a",
    level = "DEBUG"
)

from flip7_sim import play_flip7
from flip7_sim.plot import plot_game, PLOT_DIR

def main():

    parser = ArgumentParser(
        prog = "flip7",
        description = "Simulation of the Flip 7 card game",

    )

    parser.add_argument("-n", "--num-players", default=5, type=int)

    parser.add_argument("-p", "--print-logs", action="store_true")

    parser.add_argument("-s", "--save-figure", action="store_true")

    parser.add_argument("--suppress-figure", action="store_true")

    args = parser.parse_args()

    play_flip7(num_players=args.num_players)

    if not args.suppress_figure:
        plot_game(save_fig=args.save_figure)


if __name__ == "__main__":
    main()