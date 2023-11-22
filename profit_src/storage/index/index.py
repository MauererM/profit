"""Implements a class that stores values of stock market indices

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2023 Mario Mauerer
"""

import re
from ... import files
from ...storage.storage_abc import MarketDataStorage
from ...helper import create_dict_from_list


class IndexData(MarketDataStorage):
    """Represents data from a marketdata-csv.
    Index files have this format:
    index + Symbol:
    index_[a-zA-Z0-9.]{1,10}\.csv
    """

    FORMAT_FNAME_GROUPS = r'index_([a-zA-Z0-9.\^]{1,10})\.csv'

    def __init__(self, pathname, id_, data):
        # Give the symbol/id explicitly (don't derive it from the file name) -
        # this allows weird characters like ^ in the symbol, too
        self.pname = pathname
        self.id_ = id_

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
        self.index_cleaned = groups[0]

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

    def get_index(self):
        return self.index_cleaned

    def get_id(self):
        return self.id_
