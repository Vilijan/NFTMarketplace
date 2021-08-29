import streamlit as st
from src.blockchain_utils.credentials import get_client, get_account_credentials
from src.services.nft_service import NFTService
from src.services.nft_marketplace import NFTMarketplace
from src.repository.nft_repository import NFTRepository
from src.repository.marketplace_repository import NFTMarketplaceRepository
import time
import algosdk

client = get_client()

if "admin" not in st.session_state:
    st.session_state.admin = algosdk.account.generate_account()
    st.session_state.punk_3100_owner = st.session_state.admin
    st.session_state.punk_7252_owner = st.session_state.admin

if "buyer_1" not in st.session_state:
    st.session_state.buyer_1 = algosdk.account.generate_account()

if "app_is_deployed" not in st.session_state:
    st.session_state.app_is_deployed = False

if "punk_3100_image" not in st.session_state:
    st.session_state.punk3100_image = None

if "punk_7252_image" not in st.session_state:
    st.session_state.punk_7252_image = None

if "transactions" not in st.session_state:
    st.session_state.transactions = []

admin_pk, admin_address = st.session_state.admin
buyer_1_pk, buyer_1_address = st.session_state.buyer_1

st.title("Fund addresses")
st.text(f"Admin address: {admin_address}")
st.text(f"Buyer 1 address: {buyer_1_address}")

nft_repository = NFTRepository()

if "nfts_deployed" not in st.session_state:
    st.session_state.nfts_deployed = False

if "should_deploy_apps" not in st.session_state:
    st.session_state.should_deploy_apps = True

if "punk_3100" not in st.session_state:
    st.session_state.punk_3100 = NFTService(nft_creator_pk=admin_pk,
                                            nft_creator_address=admin_address,
                                            client=client,
                                            unit_name="PUNK",
                                            asset_name="Punk #3100",
                                            nft_url="https://gateway.pinata.cloud/ipfs/QmUKRAYGGDyfjKkWzKUCLEmPAQjf4TPCEsuayweGk4NhSu")

if "punk_7252" not in st.session_state:
    st.session_state.punk_7252 = NFTService(nft_creator_pk=admin_pk,
                                            nft_creator_address=admin_address,
                                            client=client,
                                            unit_name="PUNK",
                                            asset_name="Punk #7252",
                                            nft_url="https://gateway.pinata.cloud/ipfs/Qmb3FmTjuJvfcv3YczncZgBHvDMyndyZPE9bwEFb4HTd3Y")


# 1. Mint NFTS

def mint_nft_3100():
    if st.session_state.punk_3100.nft_id is None:
        tx_id = st.session_state.punk_3100.create_nft()
        st.session_state.transactions.append(f"Punk #3100 minted in {tx_id}")


def mint_nft_7252():
    if st.session_state.punk_7252.nft_id is None:
        tx_id = st.session_state.punk_7252.create_nft()
        st.session_state.transactions.append(f"Punk #7252 minted in {tx_id}")


st.title("Step 1: Mint NFTs")
buttons = st.columns(2)

if st.session_state.punk_3100.nft_id is None:
    _ = buttons[0].button("Mint Punk #3100", on_click=mint_nft_3100)
else:
    nft_id = st.session_state.punk_3100.nft_id
    if st.session_state.punk3100_image is None:
        st.session_state.punk3100_image = nft_repository.nft_image(nft_id)

    buttons[0].image(st.session_state.punk3100_image,
                     caption=f"Punk #3100 with nft_id: {nft_id}",
                     use_column_width=True)

    if "punk_3100_market" not in st.session_state:
        st.session_state.punk_3100_market = NFTMarketplace(admin_pk=admin_pk,
                                                           admin_address=admin_address,
                                                           nft_id=nft_id,
                                                           client=client)

if st.session_state.punk_7252.nft_id is None:
    _ = buttons[1].button(f"Mint Punk #7252", on_click=mint_nft_7252)
else:
    nft_id = st.session_state.punk_7252.nft_id
    if st.session_state.punk_7252_image is None:
        st.session_state.punk_7252_image = nft_repository.nft_image(st.session_state.punk_7252.nft_id)
    buttons[1].image(st.session_state.punk_7252_image,
                     caption=f"Mint Punk #7252 with nft_id: {nft_id}",
                     use_column_width=True)

    if "punk_7252_market" not in st.session_state:
        st.session_state.punk_7252_market = NFTMarketplace(admin_pk=admin_pk,
                                                           admin_address=admin_address,
                                                           nft_id=nft_id,
                                                           client=client)

st.title("Step 2: Deploy Stateful Smart Contracts that enable the buy/sell interactions")

can_deploy = ("punk_7252_market" in st.session_state) and ("punk_3100_market" in st.session_state)
if can_deploy and st.session_state.should_deploy_apps:
    st.warning("Deploying of the Stateful Smart Contracts started...")

    tx_id = st.session_state.punk_3100_market.app_initialization(nft_owner_address=admin_address)
    st.session_state.transactions.append(f"ASC1 for #3100 deployed in {tx_id}")

    tx_id = st.session_state.punk_7252_market.app_initialization(nft_owner_address=admin_address)
    st.session_state.transactions.append(f"ASC1 for #7252 deployed in {tx_id}")

    tx_id = st.session_state.punk_3100.change_nft_credentials_txn(
        escrow_address=st.session_state.punk_3100_market.escrow_address)
    st.session_state.transactions.append(f"NFT credentials changed for punk #3100 in {tx_id}")

    tx_id = st.session_state.punk_7252.change_nft_credentials_txn(
        escrow_address=st.session_state.punk_7252_market.escrow_address)
    st.session_state.transactions.append(f"NFT credentials changed for punk #3100 in {tx_id}")

    tx_id = st.session_state.punk_3100_market.initialize_escrow()
    st.session_state.transactions.append(f"Escrow for punk #3100 initialized in {tx_id}")

    tx_id = st.session_state.punk_7252_market.initialize_escrow()
    st.session_state.transactions.append(f"Escrow for punk #7252 initialized in {tx_id}")

    tx_id = st.session_state.punk_3100_market.fund_escrow()
    st.session_state.transactions.append(f"Escrow for punk #3100 funded in {tx_id}")

    tx_id = st.session_state.punk_7252_market.fund_escrow()
    st.session_state.transactions.append(f"Escrow for punk #3100 funded in {tx_id}")

    st.session_state.should_deploy_apps = False
    st.session_state.app_is_deployed = True
else:
    if not can_deploy:
        st.error("You firs need to mint the NFTs.")
    else:
        st.success("Stateful Smart Contracts were successfully deployed.")


def sell_punk_3100(sell_price: int):
    nft_owner_pk = st.session_state.punk_3100_owner[0]
    tx_id = st.session_state.punk_3100_market.make_sell_offer(sell_price=sell_price,
                                                              nft_owner_pk=nft_owner_pk)
    st.session_state.transactions.append(f"Punk #3100 is put on sale for {sell_price} micro algos in {tx_id}")


def buy_punk_3100(buy_price: int, owner_address):
    tx_id = st.session_state.punk_3100.opt_in(buyer_1_pk)
    st.session_state.transactions.append(f"Account opted-in for punk #3100 in {tx_id}")

    tx_id = st.session_state.punk_3100_market.buy_nft(nft_owner_address=owner_address,
                                                      buyer_address=buyer_1_address,
                                                      buyer_pk=buyer_1_pk,
                                                      buy_price=buy_price)
    st.session_state.transactions.append(f"Punk #3100 bought by {buyer_1_address} in {tx_id}")
    st.session_state.punk_3100_owner = st.session_state.buyer_1


def sell_punk_7252(sell_price: int):
    nft_owner_pk = st.session_state.punk_7252_owner[0]
    tx_id = st.session_state.punk_7252_market.make_sell_offer(sell_price=sell_price,
                                                              nft_owner_pk=nft_owner_pk)

    st.session_state.transactions.append(f"Punk #7252 is put on sale for {sell_price} micro algos in {tx_id}")


def buy_punk_7252(buy_price: int, owner_address):
    tx_id = st.session_state.punk_7252.opt_in(buyer_1_pk)
    st.session_state.transactions.append(f"Account opted-in for punk #7252 in {tx_id}")

    tx_id = st.session_state.punk_7252_market.buy_nft(nft_owner_address=owner_address,
                                                      buyer_address=buyer_1_address,
                                                      buyer_pk=buyer_1_pk,
                                                      buy_price=buy_price)
    st.session_state.transactions.append(f"Punk #7252 bought by {buyer_1_address} in {tx_id}")
    st.session_state.punk_7252_owner = st.session_state.buyer_1


if st.session_state.app_is_deployed:
    st.title("Step 3: Buy/Sell the NFTs")

    punk_3100_app_state = NFTMarketplaceRepository.load_app_state(st.session_state.punk_3100_market.app_id)

    st.image(st.session_state.punk3100_image,
             caption=f"Punk #3100 connected with asc1: {st.session_state.punk_3100_market.app_id}")

    if punk_3100_app_state["APP_STATE"] == 1:
        st.warning("The Punk is not on SALE")
        price_punk3100 = st.number_input(f'#3100 Price',
                                         value=1000,
                                         step=100)
        _ = st.button(f'Sale #3100 for {price_punk3100} algos', on_click=sell_punk_3100,
                      args=(price_punk3100,))
    else:
        nft_price = punk_3100_app_state["ASA_PRICE"]
        nft_seller = punk_3100_app_state["ASA_OWNER"]
        st.success(f"The Punk is on sale for: {nft_price} micro algos by: {nft_seller}")
        _ = st.button(f'Buy punk #3100', on_click=buy_punk_3100,
                      args=(nft_price, nft_seller))

    punk_7252_app_state = NFTMarketplaceRepository.load_app_state(st.session_state.punk_7252_market.app_id)

    st.image(st.session_state.punk_7252_image,
             caption=f"Punk #7252 connected with asc1: {st.session_state.punk_7252_market.app_id}")

    if punk_7252_app_state["APP_STATE"] == 1:
        st.warning("The Punk is not on SALE")
        price_punk7252 = st.number_input(f'#7252 Price',
                                         value=1000,
                                         step=100)
        _ = st.button(f'Sale #7252 for {price_punk7252} algos', on_click=sell_punk_7252,
                      args=(price_punk7252,))
    else:
        nft_price = punk_7252_app_state["ASA_PRICE"]
        nft_seller = punk_7252_app_state["ASA_OWNER"]
        st.success(f"The Punk is on sale for: {nft_price} micro algos by: {nft_seller}")
        _ = st.button(f'Buy punk #7252', on_click=buy_punk_7252,
                      args=(nft_price, nft_seller))

st.title("Executed transactions")

for tx in st.session_state.transactions:
    st.success(tx)
