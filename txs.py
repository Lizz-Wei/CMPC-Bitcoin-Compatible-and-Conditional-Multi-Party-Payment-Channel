import math
from typing import Tuple, Dict
from bitcoinutils.transactions import Transaction, TxOutput, TxInput
from bitcoinutils.script import Script
import init
import scripts


init.initNetwork()


# MPC Funding
def get_MPCTX_funding(utxos: Dict[str, TxInput], users, c: int, feerate: float, committee_num: int,
                      committee_threshold: int) -> Transaction:
    # 给通道注资
    tx_inputs = []
    # 为每个用户创建一个输入
    for key, tx_input in utxos.items():
        tx_inputs.append(tx_input)

    # 创建一个输出到P2SH地址
    tx_out = TxOutput(c * len(users), scripts.get_script_MPCTXs(users, committee_num, committee_threshold))
    tx_outputs = [tx_out]

    # 创建交易
    tx = Transaction(tx_inputs, tx_outputs)

    for i, (key, tx_input) in enumerate(utxos.items()):
        script_pub_key = users[key].p2pkh
        sig = users[key].sk.sign_input(tx, i, script_pub_key)
        tx_input.script_sig = Script([sig, users[key].pk.to_hex()])

    print("注资交易十六进制为:", tx.serialize())
    # 计算交易大小
    estimated_size = int(len(tx.serialize()) / 2)
    print(f"注资交易大小为：{estimated_size}bytes")
    # 计算交易费用
    fee = math.ceil(feerate * estimated_size)
    print(f"开启通道费用:{fee}satoshi,{fee * 61731.91 / 100000000}$")
    print(tx)
    return tx

