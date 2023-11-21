"""Implements a class that stores forex data

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

import re
import dateoperations
import stringoperations
import files
from storage.storage_abc import MarketDataStorage
from helper import create_dict_from_list


class ForexData(MarketDataStorage):
    """Represents data from a marketdata-csv.
    Forex files have this format:
    forex + Symbol A + Symbol B:
    "forex_[a-zA-Z0-9]{1,5}_[a-zA-Z0-9]{1,5}\.csv"
    """

    FORMAT_FNAME_GROUPS = r'forex_([a-zA-Z0-9]{1,5})_([a-zA-Z0-9]{1,5})\.csv'

    def __init__(self, pathname, interpol_days, data):
        self.pname = pathname
        self.interpol_days = interpol_days

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

        # From the pathname, extract the name of the file and its constituents.
        self.fname = files.get_filename_from_path(self.pname)
        match = re.match(self.FORMAT_FNAME_GROUPS, self.fname)
        groups = match.groups()
        self.symbol_a = groups[0]
        self.symbol_b = groups[1]

        self.dates_dict = create_dict_from_list(self.dates)

    def get_filename(self):
        return self.fname # Don't return the path-name

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

    def get_interpol_days(self):
        return self.interpol_days

    def get_pathname(self):
        return self.pname

    def get_symbol_a(self):
        return self.symbol_a

    def get_symbol_b(self):
        return self.symbol_b
