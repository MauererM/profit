"""Top-level entry point for PROFIT.

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import argparse
from profit_src import profit
from config import ProfitConfig


def main():
    parser = argparse.ArgumentParser(description="Process the input configuration of PROFIT")
    parser.add_argument('--days', type=int, required=False, help="Number of analysis days as a positive integer")
    parser.add_argument('--interactive', action='store_true', help="Run PROFIT in interactive mode")
    args = parser.parse_args()
    if not isinstance(args.days, int):
        args.days = None
        print("Did not receive any --days argument. Will default to DAYS_ANALYSIS value in config.py")
    if args.interactive is True:
        print("Will run PROFIT in interactive mode.")
    else:
        print("Will run PROFIT not in interactive mode (can be enabled via --interactive).")

    config = ProfitConfig()

    # Add the parsed data to the main config-class:
    config.DAYS_ANALYSIS_ARGPARSE = args.days
    config.INTERACTIVE_MODE = args.interactive

    profit.main(config)  # Launch PROFIT


if __name__ == '__main__':
    main()
