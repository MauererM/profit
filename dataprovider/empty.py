"""Implements dummy functions that do not provide data from any provider.
Done to maintain backwards-compatibility with the code (and to be able to disable the online-provider).

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2023 Mario Mauerer
"""

from dataprovider import DataProvider

class EmptyProvider(DataProvider):
    """An empty data-provider that will always be fallen back to. The calling functions handle the errors raised
    by this empty data provider themselves."""

    def __init__(self, dateformat):
        """
        Constructor:
        :param dateformat: String that encodes the format of the dates, e.g. "%d.%m.%Y"
        :param cooldown: Time in seconds between API calls
        """
        self.name = "Empty/Fallback"
        self.dateformat = dateformat

    def initialize(self):
        return True  # The empty provider (used last by dataprovider_main) must succeed here

    def get_name(self):
        return self.name

    def retrieve_forex_data(self):
        raise RuntimeError(
            "Online dataprovider not available")  # This will trigger the calling functions to fall back to other methods

    def retrieve_stock_data(self):
        raise RuntimeError(
            "Online dataprovider not available")  # This will trigger the calling functions to fall back to other methods
