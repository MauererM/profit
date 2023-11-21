from abc import ABC, abstractmethod


class DataProvider(ABC):
    """Abstract base class for a data provider.
    Every data provider package (e.g., yahoo finance) should inherit this class.
    At startup/the main module (dataprovider.py) checks the discovered subpackages if there is a class in there that
    inherits from this ABC. If yes, it uses it as data provider.
    The data provider must provide end-of-day historic data, both for stocks and forex. The granularity is always
    single days/end-of-day-data.
    """

    @abstractmethod
    def initialize(self):
        """Initializes the provider. Returns True, if the provider works, False otherwise.
        Should try to obtain test-data.
        """
        pass

    @abstractmethod
    def get_name(self):
        """Simply returns the name (as a string) of the data provider"""
        pass

    @abstractmethod
    def retrieve_forex_data(self):
        """Return forex-data for two symbols (e.g., CHF and USD).
        :param sym_a, sym_b: String of the currency symbol, as used by the data provider.
        :param startdate: stopdate: Strings for the date-interval of the desired historic data.
        :return: Two lists, one a list of strings (dates) and the corresponding forex values (list of floats)
        """
        pass

    @abstractmethod
    def retrieve_stock_data(self):
        """Return stock-data for a symbol and/or exchange
        :param symbol: String of the stock symbol, as used by the data provider.
        :param startdate: String of the start-date of the interval that should be retrieved
        :param stopdate: String of the stop-date of the interval that should be retrieved
        :param symbol_exchange: String of the exchange, e.g., "SWX". Unused in Yahoo finance, as the exchange
        is encoded in the symbol (e.g., CSGN.SW)
        :return: Two lists, one a list of strings (dates) and the corresponding stock values (list of floats)
        """
        pass
