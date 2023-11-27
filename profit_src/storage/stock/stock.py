"""Implements a class that stores market prices of stocks

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import re
from ... import files
from ...storage.storage_abc import MarketDataStorage
from ...helper import create_dict_from_list


class StockData(MarketDataStorage):
    """Represents data from a marketdata-csv.
    Stock files have this format:
    stock + Symbol + Exchange + Currency:
    stock_[a-zA-Z0-9.]{1,10}_[a-zA-Z0-9.]{1,10}_[a-zA-Z0-9]{1,5}\.csv
    """
    FORMAT_FNAME_GROUPS = r'stock_([a-zA-Z0-9.]{1,15})_([a-zA-Z0-9.]{1,15})_([a-zA-Z0-9]{1,5})\.csv'

    def __init__(self, pathname, id_, data, splits, holes):
        # Give the symbol/id explicitly (don't derive it from the file name) -
        # this allows weird characters like ^ in the symbol, too
        self.pname = pathname
        self.id_ = id_
        self.holes = holes  # If the stored data is non-contiguous, this is a list of missing dates (or an empty list)

        dates = data[0]
        values = data[1]
        # Crop the last entry out of the list; it might change after a day, due to end-of-day data and/or
        # potential extrapolation.
        if len(dates) > 1:
            self.dates = dates[0:-1]
            self.values = values[0:-1]
        else:
            self.dates = dates
            self.values = values

        self.splits = splits  # List of tuples. Normal splits have a value >1. Reverse splits have <1.

        # From the pathname, extract the name of the file and its constituents.
        self.fname = files.get_filename_from_path(self.pname)
        match = re.match(self.FORMAT_FNAME_GROUPS, self.fname)
        groups = match.groups()
        self.symbol = groups[0]
        self.exchange = groups[1]
        self.currency = groups[2]

        self.dates_dict = create_dict_from_list(self.dates)

    def get_filename(self):
        return self.fname  # Don't return the path-name

    def get_dates_dict(self):
        return self.dates_dict

    def get_dates_list(self):
        return self.dates

    def get_values(self):
        return self.values

    def get_startdate(self):
        try:
            return self.dates[0]
        except IndexError:
            return None

    def get_stopdate(self):
        try:
            return self.dates[-1]
        except IndexError:
            return None

    def get_pathname(self):
        return self.pname

    def get_symbol(self):
        return self.symbol

    def get_exchange(self):
        return self.exchange

    def get_currency(self):
        return self.currency

    def get_id(self):
        return self.id_

    def get_holes(self):
        return self.holes

    def get_splits(self):
        return self.splits
