from abc import ABC, abstractmethod


class EscrowInterface(ABC):

    @abstractmethod
    def initialize_escrow(self, escrow_address):
        pass
