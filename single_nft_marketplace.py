from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.services.nft_service import NFTService
from src.services.nft_marketplace import NFTMarketplace

client = get_client()
acc_pk, acc_address, _ = get_account_credentials(account_id=2)
nft_buyer_pk, nft_buyer_address, _ = get_account_credentials(account_id=3)

nft_service = NFTService(nft_creator_pk=acc_pk,
                         nft_creator_address=acc_address,
                         client=client,
                         unit_name="TOK",
                         asset_name="Tokility")

nft_service.create_nft()

nft_marketplace = NFTMarketplace(admin_pk=acc_pk,
                                 admin_address=acc_address,
                                 nft_id=nft_service.nft_id,
                                 client=client)

nft_marketplace.app_initialization(nft_owner_address=acc_address)

nft_service.change_nft_credentials_txn(escrow_address=nft_marketplace.escrow_address)

nft_marketplace.initialize_escrow()

nft_marketplace.fund_escrow()

nft_marketplace.make_sell_offer(sell_price=10000, nft_owner_pk=acc_pk)

nft_service.opt_in(nft_buyer_pk)

nft_marketplace.buy_nft(nft_owner_address=acc_address, buyer_address=nft_buyer_address,
                        buyer_pk=nft_buyer_pk, buy_price=10000)
