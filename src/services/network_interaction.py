import base64
from typing import Optional

from algosdk.future.transaction import SignedTransaction
from algosdk.v2client import algod


class NetworkInteraction:

    @staticmethod
    def wait_for_confirmation(client: algod.AlgodClient, txid):
        """
        Utility function to wait until the transaction is
        confirmed before proceeding.
        """
        last_round = client.status().get('last-round')
        txinfo = client.pending_transaction_info(txid)
        while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
            print("Waiting for confirmation")
            last_round += 1
            client.status_after_block(last_round)
            txinfo = client.pending_transaction_info(txid)
        print(f"Transaction {txid} confirmed in round {txinfo.get('confirmed-round')}.")
        return txinfo

    @staticmethod
    def get_default_suggested_params(client: algod.AlgodClient):
        """
        Gets default suggested params with flat transaction fee and fee amount of 1000.
        :param client:
        :return:
        """
        suggested_params = client.suggested_params()

        suggested_params.flat_fee = True
        suggested_params.fee = 1000

        return suggested_params

    @staticmethod
    def submit_asa_creation(client: algod.AlgodClient, transaction: SignedTransaction) -> Optional[int]:
        """
        Submits a ASA creation transaction to the network. If the transaction is successful the ASA's id is returned.
        :param client:
        :param transaction:
        :return:
        """
        txid = client.send_transaction(transaction)

        NetworkInteraction.wait_for_confirmation(client, txid)

        try:
            ptx = client.pending_transaction_info(txid)
            return ptx["asset-index"]
        except Exception as e:
            # TODO: Proper logging needed.
            print(e)
            print('Unsuccessful creation of Algorand Standard Asset.')

    @staticmethod
    def submit_transaction(client: algod.AlgodClient, transaction: SignedTransaction) -> Optional[str]:
        txid = client.send_transaction(transaction)

        NetworkInteraction.wait_for_confirmation(client, txid)

        return txid

    @staticmethod
    def compile_program(client: algod.AlgodClient, source_code):
        """
        :param client: algorand client
        :param source_code: teal source code
        :return:
            Decoded byte program
        """
        compile_response = client.compile(source_code)
        return base64.b64decode(compile_response['result'])
