from abc import ABC, abstractmethod

# Todo add header (also in data-provider abc), add description

class MarketDataStorage(ABC):

    @abstractmethod
    def get_filename(self):
        pass
