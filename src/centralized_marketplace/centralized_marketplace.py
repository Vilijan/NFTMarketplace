from abc import ABC
from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel
import uuid

from src.marketplace_interfaces import EscrowInterface, ResellMarketplaceInterface


class Transaction(ABC, BaseModel):
    sender: str
    arguments: Optional[List[Any]]
    receiver: Optional[str]


class AppCallTransaction(Transaction):
    app_id: int


class AssetTransferTransaction(Transaction):
    asset_amount: int
    asset_id: int


class PaymentTransaction(Transaction):
    amount: int


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

    group_transactions: Optional[List[Transaction]]

    app_state: AppState = AppState.not_initialized

    def __init__(self, asa_id: int, asa_owner: str):
        self.asa_id = asa_id
        self.asa_owner = asa_owner
        self.app_id = uuid.uuid1().int

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

    def app_call(self,
                 method_name: str,
                 app_call_transaction: AppCallTransaction,
                 group_transactions: List[Transaction]):
        self.group_transactions = group_transactions
        if method_name == self.AppMethods.buy:
            self.buy(price=app_call_transaction.arguments[0])
        elif method_name == self.AppMethods.sell:
            self.sell(price=app_call_transaction.arguments[0])
        elif method_name == self.AppMethods.initialize_escrow:
            self.initialize_escrow(escrow_address=app_call_transaction.arguments[0])
        elif method_name == self.AppMethods.stop_selling:
            self.stop_selling()
        else:
            raise ValueError("Not implemented!")

    # - EscrowInterface
    def initialize_escrow(self, escrow_address):
        if self.app_state != self.AppState.not_initialized:
            raise ValueError("The escrow address has been already initialized. Transaction rejected.")

        self.app_state = self.AppState.active
        self.escrow_address = self.group_transactions[0].arguments[0]
        print("Successful transaction!")
        print(f"The escrow address has been initialized to: {escrow_address}")
        print("-" * 50)

    # - ResellMarketplaceInterface
    def sell(self, price: int):
        if self.app_state == self.AppState.not_initialized:
            raise ValueError("The escrow address has not been initialized. Transaction rejected.")

        seller_address = self.group_transactions[0].sender
        if seller_address != self.asa_owner:
            raise ValueError(f"{self.group_transactions[0].sender} is not owner of the ASA. Transaction rejected.")

        self.asa_price = price
        self.app_state = self.AppState.selling_in_progress
        print("Successful transaction!")
        print(f"Selling for the asa_id:{self.asa_id} has been started by seller_address:{seller_address} for "
              f"asa_price:{price}")
        print("-" * 50)

    def buy(self, price: int):
        if self.app_state != self.AppState.selling_in_progress:
            raise ValueError("The ASA is not on sale!. Transaction rejected.")

        buyer_address = self.group_transactions[0].sender

        if buyer_address == self.asa_owner:
            raise ValueError(f"You already own the ASA. Transaction rejected.")

        if price < self.asa_price:
            raise ValueError(f"The asa_price is {self.asa_price} while you offered {price}.Transaction rejected.")

        if (self.group_transactions[1].sender != self.escrow_address) and \
                (self.group_transactions[1].receiver != buyer_address) and \
                (self.group_transactions[1].amount == 1) and \
                (self.group_transactions[1].asset_id == self.asa_id):
            raise ValueError("Invalid Asset Transfer. Transaction Rejected.")

        self.asa_price = price
        self.app_state = self.AppState.active
        self.asa_owner = buyer_address
        print("Successful transaction!")
        print(f"The asa_id:{self.asa_id} has been sold to buyer_address:{buyer_address} for "
              f"{price}")
        print("-" * 50)

    def stop_selling(self):
        if self.app_state != self.AppState.selling_in_progress:
            raise ValueError("The ASA is not on sale!. Transaction rejected.")

        caller_address = self.group_transactions[0].sender

        if caller_address != self.asa_owner:
            raise ValueError(f"You are not the seller of the ASA. Transaction rejected.")

        self.app_state = self.AppState.active

        print("Successful transaction!")
        print(f"The selling of the ASA with id:{self.asa_id} has been stopped.")
        print("-" * 50)
