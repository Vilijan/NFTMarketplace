from src.centralized_marketplace import SimpleMarketplaceApp, AppCallTransaction, AssetTransferTransaction

ESCROW_ADDRESS = "ESCROW_ADDRESS"
INITIAL_OWNER = "initial_owner_address"
ASA_ID = 123456789
BUYER_1 = "buyer_1_address"

# Initialization of the application.
centralized_marketplace = SimpleMarketplaceApp(asa_id=ASA_ID,
                                               asa_owner=INITIAL_OWNER)

APP_ID = centralized_marketplace.app_id

# Initialize escrow account.
initialize_escrow_txn = AppCallTransaction(sender=INITIAL_OWNER,
                                           arguments=[ESCROW_ADDRESS],
                                           app_id=APP_ID)

centralized_marketplace.app_call(method_name=SimpleMarketplaceApp.AppMethods.initialize_escrow,
                                 app_call_transaction=initialize_escrow_txn,
                                 group_transactions=[initialize_escrow_txn])

centralized_marketplace.state()

# Start selling of the ASA.
sell_price = 1000
start_selling_txn = AppCallTransaction(sender=INITIAL_OWNER,
                                       arguments=[sell_price],
                                       app_id=APP_ID)
centralized_marketplace.app_call(method_name=SimpleMarketplaceApp.AppMethods.sell,
                                 app_call_transaction=start_selling_txn,
                                 group_transactions=[start_selling_txn])
centralized_marketplace.state()

# Buy ASA
buy_price = 1000
buy_txn = AppCallTransaction(sender=BUYER_1,
                             arguments=[buy_price],
                             app_id=APP_ID)
asset_transfer_txn = AssetTransferTransaction(sender=ESCROW_ADDRESS,
                                              receiver=BUYER_1,
                                              asset_amount=1,
                                              asset_id=ASA_ID)

centralized_marketplace.app_call(method_name=SimpleMarketplaceApp.AppMethods.buy,
                                 app_call_transaction=buy_txn,
                                 group_transactions=[buy_txn, asset_transfer_txn])

centralized_marketplace.state()
