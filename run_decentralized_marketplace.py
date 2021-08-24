from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.blockchain_utils.transaction_repository import get_default_suggested_params, ApplicationTransactionRepository, \
    ASATransactionRepository, PaymentTransactionRepository
from src.services import NetworkInteraction
from algosdk import logic as algo_logic
from algosdk.future import transaction as algo_txn
from pyteal import compileTeal, Mode
from algosdk.encoding import decode_address
from src.decentralized_marketplace import SimpleMarketplaceASC1
from src.services.nft_service import NFTService
from src.decentralized_marketplace.nft_escrow import nft_escrow

client = get_client()

decentralized_marketplace_contract = SimpleMarketplaceASC1()

acc_pk, acc_address, _ = get_account_credentials(account_id=1)
nft_buyer_pk, nft_buyer_address, _ = get_account_credentials(account_id=2)

# Create ASA.
nft_1_service = NFTService(nft_creator_pk=acc_pk,
                           nft_creator_address=acc_address,
                           unit_name="TOK",
                           asset_name="Tokility")

nft1_id = nft_1_service.create_nft(client)

# Create application.

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
app_args = [
    nft1_id,
    decode_address(acc_address),
    decode_address(acc_address)
]

app_transaction = ApplicationTransactionRepository.create_application(client=client,
                                                                      creator_private_key=acc_pk,
                                                                      approval_program=approval_program_bytes,
                                                                      clear_program=clear_program_bytes,
                                                                      global_schema=decentralized_marketplace_contract.global_schema,
                                                                      local_schema=decentralized_marketplace_contract.local_schema,
                                                                      app_args=app_args)

tx_id = NetworkInteraction.submit_transaction(client,
                                              transaction=app_transaction)

transaction_response = client.pending_transaction_info(tx_id)

app_id = transaction_response['application-index']
print(f'Deployed NFTMarketplace app with app_id: {app_id}')

# Initialize escrow.

escrow_fund_program_compiled = compileTeal(nft_escrow(app_id=app_id,
                                                      asa_id=nft1_id),
                                           mode=Mode.Signature,
                                           version=4)

escrow_fund_program_bytes = NetworkInteraction.compile_program(client=client,
                                                               source_code=escrow_fund_program_compiled)

escrow_fund_address = algo_logic.address(escrow_fund_program_bytes)

app_args = [
    decentralized_marketplace_contract.AppMethods.initialize_escrow,
    decode_address(escrow_fund_address)
]

initialize_escrow_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                          caller_private_key=acc_pk,
                                                                          app_id=app_id,
                                                                          on_complete=algo_txn.OnComplete.NoOpOC,
                                                                          app_args=app_args)

tx_id = NetworkInteraction.submit_transaction(client,
                                              transaction=initialize_escrow_txn)

print(f'Escrow initialized in the NFTMarketplace ASC1.')

fund_escrow_txn = PaymentTransactionRepository.payment(client=client,
                                                       sender_address=acc_address,
                                                       receiver_address=escrow_fund_address,
                                                       amount=1000000,
                                                       sender_private_key=acc_pk,
                                                       sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client,
                                          transaction=fund_escrow_txn)

print(f'Funds submitted to the escrow address.')

# Change Management credentials.

nft_1_service.change_nft_credentials_txn(client, escrow_fund_address)

# Start selling

app_args = [
    decentralized_marketplace_contract.AppMethods.sell,
    10000
]

app_call_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                 caller_private_key=acc_pk,
                                                                 app_id=app_id,
                                                                 on_complete=algo_txn.OnComplete.NoOpOC,
                                                                 app_args=app_args,
                                                                 sign_transaction=True)

_ = NetworkInteraction.submit_transaction(client, transaction=app_call_txn)
print('NFT set on sale')

# Buyer optin

opt_in_txn = ASATransactionRepository.asa_opt_in(client=client,
                                                 sender_private_key=nft_buyer_pk,
                                                 asa_id=nft_1_service.asa_id)

opt_in_txn_id = NetworkInteraction.submit_transaction(client,
                                                      transaction=opt_in_txn)

print('Opt-in transaction completed')

# Buy nft


# 1. Application call txn
app_args = [
    decentralized_marketplace_contract.AppMethods.buy
]

app_call_txn = ApplicationTransactionRepository.call_application(client=client,
                                                                 caller_private_key=nft_buyer_pk,
                                                                 app_id=app_id,
                                                                 on_complete=algo_txn.OnComplete.NoOpOC,
                                                                 app_args=app_args,
                                                                 sign_transaction=False)

# 2. Payment transaction
asa_buy_txn = PaymentTransactionRepository.payment(client=client,
                                                   sender_address=nft_buyer_address,
                                                   receiver_address=acc_address,
                                                   amount=10000,
                                                   sender_private_key=None,
                                                   sign_transaction=False)

# 3. Asset transfer transaction
sp = get_default_suggested_params(client)
asa_transfer_txn = algo_txn.AssetTransferTxn(sender=escrow_fund_address,
                                             sp=sp,
                                             receiver=nft_buyer_address,
                                             amt=1,
                                             index=nft1_id,
                                             revocation_target=acc_address)  # current owner

# Atomic transfer
gid = algo_txn.calculate_group_id([app_call_txn,
                                   asa_buy_txn,
                                   asa_transfer_txn])

app_call_txn.group = gid
asa_buy_txn.group = gid
asa_transfer_txn.group = gid

app_call_txn_signed = app_call_txn.sign(nft_buyer_pk)

asa_buy_txn_signed = asa_buy_txn.sign(nft_buyer_pk)

asa_transfer_txn_logic_signature = algo_txn.LogicSig(escrow_fund_program_bytes)
asa_transfer_txn_signed = algo_txn.LogicSigTransaction(asa_transfer_txn, asa_transfer_txn_logic_signature)

signed_group = [app_call_txn_signed,
                asa_buy_txn_signed,
                asa_transfer_txn_signed]

txid = client.send_transactions(signed_group)
print(f'Buy asa transaction completed in: {txid}')

