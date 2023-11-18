from abc import ABC, abstractmethod

class DataProvider(ABC):

    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def retrieve_forex_data(self):
        pass

    @abstractmethod
    def retrieve_stock_data(self):
        pass