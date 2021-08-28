from abc import ABC, abstractmethod


class NFTMarketplaceInterface(ABC):

    @abstractmethod
    def initialize_escrow(self, escrow_address):
        pass

    @abstractmethod
    def make_sell_offer(self, sell_price):
        pass

    @abstractmethod
    def buy(self):
        pass

    @abstractmethod
    def stop_sell_offer(self):
        pass
