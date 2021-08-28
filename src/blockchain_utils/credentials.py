from algosdk.v2client import algod
from algosdk import account as algo_acc
import yaml
import os
from pathlib import Path
from algosdk import mnemonic
from algosdk.v2client import indexer


def get_project_root_path() -> Path:
    path = Path(os.path.dirname(__file__))
    return path.parent.parent


def load_config():
    root_path = get_project_root_path()
    config_location = os.path.join(root_path, 'config.yml')

    with open(config_location) as file:
        return yaml.full_load(file)


def get_client():
    """
    :return:
        Returns algod_client
    """
    config = load_config()

    token = config.get('client_credentials').get('token')
    address = config.get('client_credentials').get('address')
    purestake_token = {'X-Api-key': token}

    algod_client = algod.AlgodClient(token, address, headers=purestake_token)
    return algod_client


def get_indexer():
    config = load_config()

    token = config.get('client_credentials').get('token')
    headers = {'X-Api-key': token}
    my_indexer = indexer.IndexerClient(indexer_token=token,
                                       indexer_address="https://testnet-algorand.api.purestake.io/idx2",
                                       headers=headers)

    return my_indexer


def get_account_credentials(account_id: int) -> (str, str, str):
    """
    Gets the credentials for the account with number: account_id
    :param account_id: Number of the account for which we want the credentials
    :return: (str, str, str) private key, address and mnemonic
    """
    config = load_config()
    account_name = f"account_{account_id}"

    account = config.get("accounts").get(account_name)
    return account.get("private_key"), account.get("address"), account.get("mnemonic")


def get_account_with_name(account_name: str) -> (str, str, str):
    config = load_config()
    account = config.get(account_name)
    return account.get("private_key"), account.get("address"), account.get("mnemonic")


def add_account_to_config():
    """
    Adds account to the accounts list in the config.yml file.
    """
    private_key, address = algo_acc.generate_account()

    account_data = {
        "private_key": private_key,
        "address": address,
        "mnemonic": mnemonic.from_private_key(private_key)
    }

    root_path = get_project_root_path()
    config_location = os.path.join(root_path, 'config.yml')

    with open(config_location, 'r') as file:
        cur_yaml = yaml.full_load(file)
        total_accounts = cur_yaml.get("accounts").get("total")

        curr_account = total_accounts + 1
        curr_account_credentials = {
            f"account_{curr_account}": account_data
        }

        cur_yaml["accounts"].update(curr_account_credentials)
        cur_yaml["accounts"]["total"] = curr_account

    with open(config_location, 'w') as file:
        yaml.safe_dump(cur_yaml, file)
