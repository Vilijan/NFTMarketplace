from abc import ABC, abstractmethod


class ResellMarketplaceInterface(ABC):

    @abstractmethod
    def sell(self):
        pass

    @abstractmethod
    def buy(self):
        pass

    @abstractmethod
    def stop_selling(self):
        pass
