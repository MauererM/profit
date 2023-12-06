"""Top-level entry point for PROFIT.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import argparse
from profit_src import profit
from config import ProfitConfig


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--days', type=int, required=False, help="Number of analysis days as a positive integer")
    args = parser.parse_args()
    if not isinstance(args.days, int):
        args.days = None
        print("Did not receive any --days argument. Will default to DAYS_ANALYSIS value in config.py")

    config = ProfitConfig()
    profit.main(config, args.days)  # Launch PROFIT


if __name__ == '__main__':
    main()
