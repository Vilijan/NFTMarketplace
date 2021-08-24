from abc import ABC, abstractmethod
import uuid


class ResellMarketplaceInterface(ABC):

    @abstractmethod
    def sell(self, price: int):
        pass

    @abstractmethod
    def buy(self, price: int):
        pass

    @abstractmethod
    def stop_selling(self):
        pass
