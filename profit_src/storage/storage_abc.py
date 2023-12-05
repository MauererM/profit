"""Storage-classes (stocks, forex, indices) must adhere to this ABC

PROFIT - Python-Based Return on Investment and Financial Investigation Tool
MIT License
Copyright (c) 2018-2023 Mario Mauerer
"""

from abc import ABC, abstractmethod


class MarketDataStorage(ABC):
    """The ABC for the data storage classes (e.g., stock, forex, indices)"""

    @abstractmethod
    def get_filename(self):
        pass

    @abstractmethod
    def get_dates_dict(self):
        pass

    @abstractmethod
    def get_dates_list(self):
        pass

    @abstractmethod
    def get_values(self):
        pass

    @abstractmethod
    def get_startdate(self):
        pass

    @abstractmethod
    def get_stopdate(self):
        pass

    @abstractmethod
    def get_pathname(self):
        pass

    @abstractmethod
    def get_id(self):
        pass

    @abstractmethod
    def get_holes(self):
        pass

    @abstractmethod
    def get_splits(self):
        pass

    @abstractmethod
    def get_overwrite_flag(self):
        pass
