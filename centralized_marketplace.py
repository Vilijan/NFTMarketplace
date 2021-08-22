from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum


class EscrowInterface(ABC):

    @abstractmethod
    def initialize_escrow(self, escrow_address):
        pass


class ResellMarketplaceInterface(ABC):

    @abstractmethod
    def sell(self, algo_amount: int):
        pass

    @abstractmethod
    def buy(self, algo_amount: int):
        pass

    @abstractmethod
    def stop_selling(self):
        pass


class SimpleMarketplaceApp(EscrowInterface, ResellMarketplaceInterface):
    class AppMethods:
        init = "init"
        initialize_escrow = "initialize_escrow"
        sell = "sell"
        buy = "buy"
        stop_selling = "stop_selling"

    class AppState(Enum):
        not_initialized = 0
        active = 1
        selling_in_progress = 2

    escrow_address: Optional[str]
    asa_id: int
    asa_price: Optional[int]
    asa_owner: str

    app_state: AppState = AppState.not_initialized

    def __init__(self, asa_id: int, asa_owner: str):
        self.asa_id = asa_id
        self.asa_owner = asa_owner

    def state(self):
        print(f'APP UI')
        print(f'asa_id: {self.asa_id}')
        print(f'asa_owner: {self.asa_owner}')

        if self.app_state == self.AppState.not_initialized:
            print("The application is not initialized")
        elif self.app_state == self.AppState.active:
            print(f"The ASA is not on sale by {self.asa_owner}")
        elif self.app_state == self.AppState.selling_in_progress:
            print(f"The ASA is on sale for {self.asa_price} by {self.asa_owner}")
        else:
            print("SOMETHING IS WRONG!!!!")
        print('-' * 50)

    # - EscrowInterface
    def initialize_escrow(self, escrow_address):
        if self.app_state != self.AppState.not_initialized:
            raise ValueError("The escrow address has been already initialized. Transaction rejected.")

        self.app_state = self.AppState.active
        print("Successful transaction!")
        print(f"The escrow address has been initialized to: {escrow_address}")
        print("-" * 50)

    # - ResellMarketplaceInterface
    def sell(self, seller_address: str, asa_price: int):
        if self.app_state == self.AppState.not_initialized:
            raise ValueError("The escrow address has not been initialized. Transaction rejected.")

        if seller_address != self.asa_owner:
            raise ValueError(f"{seller_address} is not owner of the ASA. Transaction rejected.")

        self.asa_price = asa_price
        self.app_state = self.AppState.selling_in_progress
        print("Successful transaction!")
        print(f"Selling for the asa_id:{self.asa_id} has been started by seller_address:{seller_address} for "
              f"asa_price:{asa_price}")
        print("-" * 50)

    def buy(self, buyer_address: str, amount: int):
        if self.app_state != self.AppState.selling_in_progress:
            raise ValueError("The ASA is not on sale!. Transaction rejected.")

        if buyer_address == self.asa_owner:
            raise ValueError(f"You already own the ASA. Transaction rejected.")

        if amount < self.asa_price:
            raise ValueError(f"The asa_price is {self.asa_price} while you offered {amount}.Transaction rejected.")

        self.asa_price = amount
        self.app_state = self.AppState.active
        self.asa_owner = buyer_address
        print("Successful transaction!")
        print(f"The asa_id:{self.asa_id} has been sold to buyer_address:{buyer_address} for "
              f"{amount}")
        print("-" * 50)

    def stop_selling(self, caller_address: str):
        if self.app_state != self.AppState.selling_in_progress:
            raise ValueError("The ASA is not on sale!. Transaction rejected.")

        if caller_address != self.asa_owner:
            raise ValueError(f"You are not the seller of the ASA. Transaction rejected.")

        self.app_state = self.AppState.active

        print("Successful transaction!")
        print(f"The selling of the ASA with id:{self.asa_id} has been stopped.")
        print("-" * 50)


ESCROW_ADDRESS = "ESCROW_ADDRESS"

centralized_marketplace = SimpleMarketplaceApp(asa_id=123456789,
                                               asa_owner="wawa_address")

centralized_marketplace.initialize_escrow(escrow_address=ESCROW_ADDRESS)
centralized_marketplace.state()

centralized_marketplace.sell(seller_address="wawa_address", asa_price=2000)
centralized_marketplace.state()

centralized_marketplace.buy(buyer_address="pudge_address", amount=2000)
centralized_marketplace.state()
