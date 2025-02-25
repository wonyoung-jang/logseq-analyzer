import cProfile
import pstats
from pstats import SortKey
from src.app import run_app

def main():
    profiler = cProfile.Profile()
    profiler.enable()

    run_app()

    profiler.disable()
    stats = pstats.Stats(profiler).strip_dirs().sort_stats(SortKey.CUMULATIVE)
    stats.dump_stats("profile_output.prof")
    stats.print_stats(20)
    # stats.print_callers(10)
    # stats.print_callees(10)

if __name__ == "__main__":
    main()
