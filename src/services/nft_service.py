from src.services import NetworkInteraction
from src.blockchain_utils.transaction_repository import ASATransactionRepository


class NFTService:

    def __init__(self,
                 nft_creator_address: str,
                 nft_creator_pk: str,
                 unit_name: str,
                 asset_name: str,
                 nft_url=None):
        self.nft_creator_address = nft_creator_address
        self.nft_creator_pk = nft_creator_pk
        self.unit_name = unit_name
        self.asset_name = asset_name
        self.nft_url = nft_url

        self.asa_id = None

    def create_nft(self, client):
        signed_txn = ASATransactionRepository.create_non_fungible_asa(client=client,
                                                                      creator_private_key=self.nft_creator_pk,
                                                                      unit_name=self.unit_name,
                                                                      asset_name=self.asset_name,
                                                                      note=None,
                                                                      manager_address=self.nft_creator_address,
                                                                      reserve_address=self.nft_creator_address,
                                                                      freeze_address=self.nft_creator_address,
                                                                      clawback_address=self.nft_creator_address,
                                                                      url=self.nft_url,
                                                                      default_frozen=True,
                                                                      sign_transaction=True)

        asa_id = NetworkInteraction.submit_asa_creation(client=client, transaction=signed_txn)
        self.asa_id = asa_id
        return asa_id

    def change_nft_credentials_txn(self, client, escrow_address):
        # TODO: This should return the transaction.
        txn = ASATransactionRepository.change_asa_management(client=client,
                                                             current_manager_pk=self.nft_creator_pk,
                                                             asa_id=self.asa_id,
                                                             manager_address="",
                                                             reserve_address="",
                                                             freeze_address="",
                                                             strict_empty_address_check=False,
                                                             clawback_address=escrow_address,
                                                             sign_transaction=True)

        _ = NetworkInteraction.submit_transaction(client,
                                                  transaction=txn)
