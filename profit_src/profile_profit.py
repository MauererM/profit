"""Implements a profiler to find performance bottlenecks.
Works best if the whole file is simply copied to where profit_main.py resides (no need then to adapt relative paths).

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import cProfile
from pstats import Stats
from profit_src.profit import main as dut_main
from config import ProfitConfig

# Note: Run this from the top-level directory (where profit_main.py) resides! It is stored here as it is a debug-tool.

if __name__ == "__main__":
    # Create a profiler object
    profiler = cProfile.Profile()

    profiler.enable()
    config = ProfitConfig()
    dut_main(config)
    profiler.disable()

    stats = Stats(profiler)
    stats.sort_stats('cumtime').print_stats(100)
