import cProfile
import pstats
from pstats import SortKey
from src.app import run_app

def main():
    profiler = cProfile.Profile()
    profiler.enable()

    run_app()

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats(SortKey.CUMULATIVE)
    stats.dump_stats("profile_output.prof")
    stats.print_stats()
    # stats.print_callers()
    # stats.print_callees()

if __name__ == "__main__":
    main()
