import cProfile
import pstats
from pstats import SortKey
from src.app import run


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    run()

    profiler.disable()

    with open("profile_output.txt", "w") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs().sort_stats(SortKey.CUMULATIVE)
        stats.print_stats()
        stats.dump_stats("profile_output.prof")


if __name__ == "__main__":
    main()
