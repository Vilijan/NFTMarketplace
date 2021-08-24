from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository, \
    ASATransactionRepository, PaymentTransactionRepository
from src.services import NetworkInteraction
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from algosdk.encoding import decode_address
from src.decentralized_marketplace import SimpleMarketplaceASC1

client = get_client()

decentralized_marketplace_contract = SimpleMarketplaceASC1()

acc_pk, acc_address, _ = get_account_credentials(account_id=1)

approval_program_compiled = compileTeal(decentralized_marketplace_contract.approval_program(),
                                        mode=Mode.Application,
                                        version=4)

clear_program_compiled = compileTeal(decentralized_marketplace_contract.clear_program(),
                                     mode=Mode.Application,
                                     version=4)

approval_program_bytes = NetworkInteraction.compile_program(client=client,
                                                            source_code=approval_program_compiled)

clear_program_bytes = NetworkInteraction.compile_program(client=client,
                                                         source_code=clear_program_compiled)

global_schema = algo_txn.StateSchema(num_uints=5,
                                     num_byte_slices=4)

local_schema = algo_txn.StateSchema(num_uints=0,
                                    num_byte_slices=0)

app_args = [
    15921880,
    decode_address(acc_address)
]

app_transaction = ApplicationTransactionRepository.create_application(client=client,
                                                                      creator_private_key=acc_pk,
                                                                      approval_program=approval_program_bytes,
                                                                      clear_program=clear_program_bytes,
                                                                      global_schema=global_schema,
                                                                      local_schema=local_schema,
                                                                      app_args=app_args)

tx_id = NetworkInteraction.submit_transaction(client,
                                              transaction=app_transaction)

transaction_response = client.pending_transaction_info(tx_id)

app_id = transaction_response['application-index']
print(f'Deployed Tokility app with app_id: {app_id}')
