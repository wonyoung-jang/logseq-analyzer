import cProfile
import pstats
from pstats import SortKey
from src.app import run_app


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    run_app()

    profiler.disable()

    with open("profile_output.txt", "w") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs().sort_stats(SortKey.CUMULATIVE)
        stats.print_stats()
        stats.dump_stats("profile_output.prof")


if __name__ == "__main__":
    main()
