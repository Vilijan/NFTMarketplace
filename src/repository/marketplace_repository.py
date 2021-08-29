from src.blockchain_utils.credentials import get_indexer
import base64
from algosdk.encoding import encode_address
import time


def decode_state_parameter(param_value):
    return base64.b64decode(param_value).decode('utf-8')


class NFTMarketplaceRepository:
    @staticmethod
    def load_app_state(app_id: int):
        time.sleep(5)
        indexer = get_indexer()
        response = indexer.search_applications(application_id=app_id)
        state = dict()
        for state_k in response['applications'][0]['params']['global-state']:
            key = decode_state_parameter(state_k['key'])
            if state_k['value']['type'] == 1:
                state[key] = encode_address(base64.b64decode(state_k['value']['bytes']))
            else:
                state[key] = state_k['value']['uint']
        return state
