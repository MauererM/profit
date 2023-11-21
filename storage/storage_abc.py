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
        return self.dates

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
    def get_interpol_days(self):
        pass

    @abstractmethod
    def get_pathname(self):
        pass

