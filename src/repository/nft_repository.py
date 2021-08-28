from src.blockchain_utils.credentials import get_indexer


class NFTRepository:
    def __init__(self):
        self.indexer = get_indexer()

    def nft_image(self, nft_id: int):
        response = self.indexer.search_assets(asset_id=nft_id)
        return response["assets"][0]["params"]["url"]

    def nft_owner(self, nft_id: int):
        response = self.indexer.asset_balances(asset_id=nft_id)
        return response["balances"][0]["address"]
