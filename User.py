from typing import Dict

from bitcoinutils.keys import PrivateKey, PublicKey, P2pkhAddress
from bitcoinutils.transactions import Transaction, TxOutput, TxInput
import init

init.initNetwork()

class User:
    def __init__(self, name: str, user_info: Dict[str, str], is_committee_member: bool = False):
        self.name = name
        self.address = user_info['address']
        self.private_key = user_info['private_key']
        self.public_key = user_info['public_key']
        self.sk = PrivateKey(self.private_key)
        self.pk = PublicKey(self.public_key)
        self.p2pkh = P2pkhAddress(self.address).to_script_pub_key()
        self.is_committee_member = is_committee_member

    def create_transaction(self, tx_in: str, distribution: Dict[str, int], redeem_script: Dict[str, str]):
        # 创建新交易
        tx_outs = [TxOutput(int(amount), redeem_script) for address, amount in
                   distribution.items()]
        tx = Transaction([tx_in], tx_outs)
        return tx

    def sign_transaction(self, tx: Transaction, input_index: int, existing_signatures=None):
        if existing_signatures is None:
            existing_signatures = []
        sig = self.sk.sign_input(tx, input_index, self.p2pkh)
        new_signatures = existing_signatures + [sig]
        return new_signatures

