from pyteal import *

from src.marketplace_interfaces import EscrowInterface, ResellMarketplaceInterface


class SimpleMarketplaceASC1(EscrowInterface, ResellMarketplaceInterface):
    class Variables:
        escrow_address = Bytes("ESCROW_ADDRESS")
        asa_id = Bytes("ASA_ID")
        asa_price = Bytes("ASA_PRICE")
        asa_owner = Bytes("ASA_OWNER")
        app_state = Bytes("APP_STATE")

    class AppMethods:
        initialize_escrow = "initialize_escrow"
        sell = "sell"
        buy = "buy"
        stop_selling = "stop_selling"

    class AppState:
        not_initialized = Int(0)
        active = Int(1)
        selling_in_progress = Int(2)

    def application_start(self):
        is_app_initialization = Txn.application_id() == Int(0)

        actions = Cond(
            [Txn.application_args[0] == Bytes(self.AppMethods.buy), self.buy()],
            [Txn.application_args[0] == Bytes(self.AppMethods.initialize_escrow), self.initialize_escrow()],
            [Txn.application_args[0] == Bytes(self.AppMethods.stop_selling), self.stop_selling()],
            [Txn.application_args[0] == Bytes(self.AppMethods.sell), self.sell()]
        )

        return If(is_app_initialization) \
            .Then(self.app_initialization()).Else(actions)

    def app_initialization(self):
        asa_id = Btoi(Txn.application_args[0])
        asa_owner = Txn.application_args[1]

        return Seq([
            Assert(Txn.application_args.length() == Int(2)),
            App.globalPut(self.Variables.app_state, self.AppState.not_initialized),
            App.globalPut(self.Variables.asa_id, asa_id),
            App.globalPut(self.Variables.asa_owner, asa_owner),
            Return(Int(1))
        ])

    def initialize_escrow(self):
        escrow_address = App.globalGetEx(Int(0), self.Variables.escrow_address)

        setup_failed = Seq([
            Return(Int(0))
        ])

        setup_escrow = Seq([
            App.globalPut(self.Variables.escrow_address, Txn.application_args[1]),
            App.globalPut(self.Variables.app_state, self.AppState.active),
            Return(Int(1))
        ])

        return Seq([
            escrow_address,
            If(escrow_address.hasValue()).Then(setup_failed).Else(setup_escrow)
        ])

    def sell(self):
        is_app_active = Or(App.globalGet(self.Variables.app_state) == self.AppState.active,
                           App.globalGet(self.Variables.app_state) == self.AppState.selling_in_progress)

        is_valid_seller = Txn.sender() == App.globalGet(self.Variables.asa_owner)
        can_sell = And(is_app_active, is_valid_seller)

        update_state = Seq([
            App.globalPut(self.Variables.asa_price, Btoi(Txn.application_args[1])),
            App.globalPut(self.Variables.app_state, self.AppState.selling_in_progress),
            Return(Int(1))
        ])

        return If(can_sell).Then(update_state).Else(Return(Int(0)))

    def buy(self):
        return Return(Int(0))

    def stop_selling(self):
        return Return(Int(0))

    def approval_program(self):
        return self.application_start()

    def clear_program(self):
        return Return(Int(1))
