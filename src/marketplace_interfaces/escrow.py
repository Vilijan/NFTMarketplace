from abc import ABC, abstractmethod


class EscrowInterface(ABC):

    @abstractmethod
    def initialize_escrow(self):
        pass
