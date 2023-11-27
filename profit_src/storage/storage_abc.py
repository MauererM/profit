from abc import ABC, abstractmethod


# Todo add header (also in data-provider abc), add description

class MarketDataStorage(ABC):

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
