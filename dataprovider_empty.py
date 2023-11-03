"""Implements dummy functions that do not provide data from any provider.
Done to maintain backwards-compatibility with the code (and to be able to disable the online-provider).

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2023 Mario Mauerer
"""
class Dataprovider:

    def __init__(self, dateformat, cooldown):
        """
        Constructor:
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :param cooldown: Time in seconds between API calls
        """

        self.dateformat = dateformat
        self.cooldown = cooldown

    def get_forex_data(self, sym_a, sym_b, startdate, stopdate):
        raise RuntimeError("Online dataprovider not available")

    def get_stock_data(self, sym_stock, sym_exchange, startdate, stopdate):
        raise RuntimeError("Online dataprovider not available")