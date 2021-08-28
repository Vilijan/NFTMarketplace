from src.blockchain_utils.credentials import get_client, get_account_credentials, get_account_with_name
from src.models.asset_configurations import ASAEconomyConfiguration, ASAInitialOfferingConfiguration, ASAConfiguration
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository, \
    ASATransactionRepository, PaymentTransactionRepository
from src.services import NetworkInteraction
from src.smart_contracts.tokility_asc1 import approval_program, clear_program, AppVariables, AppMethods
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from src.smart_contracts.tokility_escrow import asa_escrow
from algosdk.encoding import decode_address
from algosdk.v2client import algod


class TokilityMarketplaceService:
    def __init__(self,
                 asa_configuration: ASAConfiguration,
                 app_creator_pk: str,
                 app_creator_address: str,
                 asa_creator_pk: str,
                 asa_creator_address: str,
                 client: algod.AlgodClient,
                 teal_version: int = 4):
        self.asa_configuration = asa_configuration
        self.app_creator_pk = app_creator_pk
        self.app_creator_address = app_creator_address
        self.asa_creator_pk = asa_creator_pk
        self.asa_creator_address = asa_creator_address
        self.client = client
        self.teal_version = teal_version

        self.app_id = None
        self.escrow_address = None
        self.escrow_program_bytes = None

    def deploy_application(self):
        approval_program_compiled = compileTeal(approval_program(asa_configuration=self.asa_configuration),
                                                mode=Mode.Application,
                                                version=self.teal_version)

        clear_program_compiled = compileTeal(clear_program(),
                                             mode=Mode.Application,
                                             version=self.teal_version)

        approval_program_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                    source_code=approval_program_compiled)

        clear_program_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                 source_code=clear_program_compiled)

        global_schema = algo_txn.StateSchema(num_uints=AppVariables.number_of_global_ints(),
                                             num_byte_slices=AppVariables.number_of_global_bytes())

        local_schema = algo_txn.StateSchema(num_uints=AppVariables.number_of_local_ints(),
                                            num_byte_slices=AppVariables.number_of_local_bytes())

        app_txn = ApplicationTransactionRepository.create_application(client=self.client,
                                                                      creator_private_key=self.app_creator_pk,
                                                                      approval_program=approval_program_bytes,
                                                                      clear_program=clear_program_bytes,
                                                                      global_schema=global_schema,
                                                                      local_schema=local_schema,
                                                                      app_args=None)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=app_txn)

        transaction_response = self.client.pending_transaction_info(tx_id)

        app_id = transaction_response['application-index']
        print(
            f'Deployed Tokility Marketplace ASC1 with app_id: {app_id} '
            f'that interacts with asa_id: {self.asa_configuration.asa_id}')
        print(f'transaction_id: {tx_id}')
        print('-' * 50)

    def setup_escrow(self):
        escrow_fund_program_compiled = compileTeal(asa_escrow(app_id=self.app_id,
                                                              asa_configuration=self.asa_configuration),
                                                   mode=Mode.Signature,
                                                   version=self.teal_version)

        self.escrow_program_bytes = NetworkInteraction.compile_program(client=self.client,
                                                                       source_code=escrow_fund_program_compiled)

        self.escrow_address = algo_logic.address(self.escrow_program_bytes)

        app_args = [
            AppMethods.initialize_escrow,
            decode_address(self.escrow_address)
        ]

        initialize_escrow_txn = ApplicationTransactionRepository.call_application(client=self.client,
                                                                                  caller_private_key=self.app_creator_pk,
                                                                                  app_id=self.app_id,
                                                                                  on_complete=algo_txn.OnComplete.NoOpOC,
                                                                                  app_args=app_args)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=initialize_escrow_txn)

        print(f'Escrow initialized in the Tokility ASC1 with transaction: {tx_id}')

        fund_escrow_txn = PaymentTransactionRepository.payment(client=self.client,
                                                               sender_address=self.app_creator_address,
                                                               receiver_address=self.escrow_address,
                                                               amount=300000,
                                                               sender_private_key=self.app_creator_pk,
                                                               sign_transaction=True)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=fund_escrow_txn)

        print(f'Fee funds submitted to the escrow address with transaction: {tx_id}')
        print('-' * 50)

    def change_asa_management(self):
        change_asa_management_txn = ASATransactionRepository.change_asa_management(client=self.client,
                                                                                   current_manager_pk=self.asa_creator_pk,
                                                                                   asa_id=self.asa_configuration.asa_id,
                                                                                   manager_address="",
                                                                                   reserve_address="",
                                                                                   freeze_address="",
                                                                                   strict_empty_address_check=False,
                                                                                   clawback_address=self.escrow_address)

        tx_id = NetworkInteraction.submit_transaction(self.client,
                                                      transaction=change_asa_management_txn)

        print(f'ASA management has been updated with transaction: {tx_id}')
        print('-' * 50)
