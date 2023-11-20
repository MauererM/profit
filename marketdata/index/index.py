"""Implements a class that stores values of stock market indices

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2023 Mario Mauerer
"""

import re
import files
from marketdata.marketdata_abc import MarketDataStorage

class IndexData(MarketDataStorage):
    """Represents data from a marketdata-csv.
    Index files have this format:
    index + Symbol:
    "index_[a-zA-Z0-9.]{1,10}\.csv"
    """

    FORMAT_FNAME_GROUPS = r'index_([a-zA-Z0-9.]{1,10})\.csv'

    def __init__(self, pathname, interpol_days, data):
        self.pname = pathname
        self.interpol_days = interpol_days
        self.dates = data[0]
        self.values = data[1]

        # From the pathname, extract the name of the file and its constituents.
        self.fname = files.get_filename_from_path(self.pname)
        match = re.match(self.FORMAT_FNAME_GROUPS, self.fname)
        groups = match.groups()
        self.index = groups[0]

    def get_filename(self):
        return self.fname # Don't return the path-name