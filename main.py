from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.services.nft_service import NFTService
from src.services.nft_marketplace import NFTMarketplace

client = get_client()
admin_pk, admin_addr, _ = get_account_credentials(1)
buyer_pk, buyer_addr, _ = get_account_credentials(2)

nft_service = NFTService(nft_creator_address=admin_addr,
                         nft_creator_pk=admin_pk,
                         client=client,
                         asset_name="Algobot",
                         unit_name="Algobot")

nft_service.create_nft()

nft_marketplace_service = NFTMarketplace(admin_pk=admin_pk,
                                         admin_address=admin_addr,
                                         client=client,
                                         nft_id=nft_service.nft_id)

nft_marketplace_service.app_initialization(nft_owner_address=admin_addr)

nft_service.change_nft_credentials_txn(escrow_address=nft_marketplace_service.escrow_address)

nft_marketplace_service.initialize_escrow()
nft_marketplace_service.fund_escrow()
nft_marketplace_service.make_sell_offer(sell_price=100000, nft_owner_pk=admin_pk)

nft_service.opt_in(buyer_pk)

nft_marketplace_service.buy_nft(nft_owner_address=admin_addr,
                                buyer_address=buyer_addr,
                                buyer_pk=buyer_pk,
                                buy_price=100000)
