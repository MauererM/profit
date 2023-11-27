"""Implements a profiler to find performance bottlenecks.
Works best if the whole file is simply copied to where profit_main.py resides (no need then to adapt relative paths).

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import cProfile
from pstats import Stats
from profit_src.profit import main as dut_main

script = "profit.py"
METHOD = "exec"

if __name__ == "__main__":
    # Create a profiler object
    profiler = cProfile.Profile()

    profiler.enable()
    dut_main()
    profiler.disable()

    stats = Stats(profiler)
    stats.sort_stats('cumtime').print_stats(100)