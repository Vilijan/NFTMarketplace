from src.services import NetworkInteraction
from src.blockchain_utils.transaction_repository import ASATransactionRepository


class NFTService:
    def __init__(
            self,
            nft_creator_address: str,
            nft_creator_pk: str,
            client,
            unit_name: str,
            asset_name: str,
            nft_url=None,
    ):
        self.nft_creator_address = nft_creator_address
        self.nft_creator_pk = nft_creator_pk
        self.client = client

        self.unit_name = unit_name
        self.asset_name = asset_name
        self.nft_url = nft_url

        self.nft_id = None

    def create_nft(self):
        signed_txn = ASATransactionRepository.create_non_fungible_asa(
            client=self.client,
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
            sign_transaction=True,
        )

        nft_id, tx_id = NetworkInteraction.submit_asa_creation(
            client=self.client, transaction=signed_txn
        )
        self.nft_id = nft_id
        return tx_id

    def change_nft_credentials_txn(self, escrow_address):
        txn = ASATransactionRepository.change_asa_management(
            client=self.client,
            current_manager_pk=self.nft_creator_pk,
            asa_id=self.nft_id,
            manager_address="",
            reserve_address="",
            freeze_address="",
            strict_empty_address_check=False,
            clawback_address=escrow_address,
            sign_transaction=True,
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=txn)

        return tx_id

    def opt_in(self, account_pk):
        opt_in_txn = ASATransactionRepository.asa_opt_in(
            client=self.client, sender_private_key=account_pk, asa_id=self.nft_id
        )

        tx_id = NetworkInteraction.submit_transaction(self.client, transaction=opt_in_txn)
        return tx_id
