import binascii
import json
import math
import time
import hashlib
from typing import Dict

from bitcoinutils.script import Script
from bitcoinutils.transactions import TxInput

import txs
import scripts
from User import User

# 定义常量
SATOSHIS_PER_BTC = 100_000_000


def main(user_num, committee_num, committee_threshold):
    with open("users_96.txt", "r") as f:
        user_list = json.load(f)

    users, utxos, selected_users = initialize_users(user_num, user_list)
    layer1, layer2, layer3, committee = split_users(users, selected_users, user_num, committee_num)

    distribution = {key: 1.0 * SATOSHIS_PER_BTC for key in users}

    c = 1 * SATOSHIS_PER_BTC
    feerate = 15.922
    TXf_MPC = txs.get_MPCTX_funding(utxos, users, c, feerate, committee_num, committee_threshold)
    txf_id = hash256(TXf_MPC.serialize())
    log_filename = f"output_{user_num}_{committee_num}_log.txt"
    with open(log_filename, "w") as log_file:
        log_file.write(f"注资交易ID为：{txf_id}\n")
        tx_in_channel = TxInput(txf_id, 0)

        start_total_time = time.perf_counter()

        total_size_1 = 0
        total_time_1 = 0
        for sender_key, sender in layer1.items():
            size, time_spent, distribution, tx = process_payment(log_file, sender_key, sender, tx_in_channel,
                                                                 distribution,
                                                                 users, committee, committee_num,
                                                                 committee_threshold,
                                                                 recipients=layer2)
            total_size_1 += size
            total_time_1 += time_spent
        log_file.write(
            f"第一层向第二层的支付通信量大小为：{total_size_1} bytes, 创建交易和签名的总时间为：{total_time_1:.6f} s\n")

        total_size_2 = 0
        total_time_2 = 0
        for sender_key, sender in layer2.items():
            size, time_spent, distribution, tx = process_payment(log_file, sender_key, sender, tx_in_channel,
                                                                 distribution,
                                                                 users, committee, committee_num,
                                                                 committee_threshold,
                                                                 recipients=layer3)
            total_size_2 += size
            total_time_2 += time_spent
        log_file.write(
            f"第二层向第三层的支付通信量大小为：{total_size_2} bytes, 创建交易和签名的总时间为：{total_time_2:.6f} s\n")
        tx_size = int(len(tx.serialize()) / 2)
        print(f"关闭通道交易大小为{tx_size}bytes")
        # 计算交易费用
        fee = math.ceil(feerate * tx_size)
        print(f"关闭通道的费用为: {fee}satoshi,{fee * 61731 / 100000000}$")
        total_size = total_size_1 + total_size_2
        total_time = total_time_1 + total_time_2
        end_total_time = time.perf_counter()
        total_duration = end_total_time - start_total_time

        log_file.write(f"总通信量大小为：{total_size} bytes\n")
        log_file.write(f"创建交易和签名的总时间为：{total_time:.6f} s\n")
        log_file.write(f"完成所有支付所需总时间为：{total_duration:.6f} s\n")
        log_file.write('----------------------------------\n')
        print(f"更新总通信量大小为：{total_size} bytes\n")
        print(f"创建交易和签名的总时间为：{total_time:.6f} s\n")
        print(f"完成所有支付所需总时间为：{total_duration:.6f} s\n")
        print('----------------------------------\n')


def initialize_users(user_num, user_list):
    users = {}
    utxos = {}
    selected_users = dict(list(user_list.items())[:user_num])
    for key, user in selected_users.items():
        users[key] = User(key, user, is_committee_member=False)
        utxos[key] = TxInput(user["utxos"][0]["txid"], user["utxos"][0]["vout"])
    return users, utxos, selected_users


def split_users(users, selected_users, user_num, committee_num):
    layer1 = {}
    layer2 = {}
    layer3 = {}
    committee = {}
    for i, key in enumerate(selected_users):
        if i < committee_num:
            committee[key] = users[key]
            committee[key].is_committee_member = True
        if i < user_num // 3:
            layer1[key] = users[key]
        elif i < 2 * user_num // 3:
            layer2[key] = users[key]
        else:
            layer3[key] = users[key]
    return layer1, layer2, layer3, committee


def process_payment(log_file, sender_key, sender, tx_in_channel, distribution, users, committee, committee_num,
                    committee_threshold, recipients):
    total_size = 0
    total_time = 0

    payments = {receiver_key: 0.01 for receiver_key in recipients.keys()}
    condition = {receiver_key: {"num": 1000} for receiver_key in recipients.keys()}
    distribution = update_distribution(distribution, sender_key, payments)
    log_file.write(f"更新的分布: {distribution}\n")

    start_time = time.perf_counter()
    redeem_script = scripts.get_script_MPCTXs(users, committee_num, committee_threshold)
    tx = sender.create_transaction(tx_in_channel, distribution, redeem_script)
    creation_time = time.perf_counter() - start_time
    log_file.write(f"创建交易时间: {creation_time:.6f} s\n")

    start_time = time.perf_counter()
    sig_s = sender.sign_transaction(tx, 0)
    signing_time_s = time.perf_counter() - start_time
    log_file.write(f"发送方{sender_key}签名时间: {signing_time_s:.6f} s\n")

    content_tocr = {"tx": tx.serialize(), "sig_s": sig_s, "condition": condition}
    content_tocr_json = json.dumps(content_tocr)
    content_tocr_size = len(content_tocr_json.encode('utf-8'))
    content_tocr_size_total = content_tocr_size * (committee_num + len(recipients))
    log_file.write(f"发送方广播总字节数: {content_tocr_size_total} bytes\n")

    first_receiver_key = next(iter(recipients))
    first_receiver = recipients[first_receiver_key]
    start_time = time.perf_counter()
    sig_r = first_receiver.sign_transaction(tx, 0, sig_s)
    signing_time_r = time.perf_counter() - start_time
    log_file.write(f"{first_receiver_key}签名时间: {signing_time_r:.6f} s\n")

    content_r1toc = {"sig_r": sig_r, "num": 1000}
    content_r1toc_json = json.dumps(content_r1toc)
    content_r1toc_size = len(content_r1toc_json.encode('utf-8'))
    content_rtoc_size_total = content_r1toc_size * committee_num
    log_file.write(f"接收方广播总字节数: {content_rtoc_size_total} bytes\n")

    sig_committee = []
    total_committee_broadcast_size = 0
    total_signing_time_c = 0
    previous_sig = sig_r
    for j, (committee_key, committee_member) in enumerate(committee.items()):
        if j >= committee_threshold:
            break
        start_time = time.perf_counter()
        sig_c = committee_member.sign_transaction(tx, 0, previous_sig)
        signing_time_c = time.perf_counter() - start_time
        total_signing_time_c += signing_time_c
        log_file.write(f"委员会成员{committee_key}签名时间: {signing_time_c:.6f} s\n")
        previous_sig = sig_c  # 使用当前签名作为下一个签名的基础

        sig_committee.append(sig_c)
        if len(sig_committee) < committee_threshold:
            content_to_otherc = {"sig_c": sig_c}
            content_to_otherc_json = json.dumps(content_to_otherc)
            content_to_otherc_size = len(content_to_otherc_json.encode('utf-8'))
            remaining_committee_members = committee_num - len(sig_committee)
            content_to_otherc_total = content_to_otherc_size * remaining_committee_members
            total_committee_broadcast_size += content_to_otherc_total
            log_file.write(f"委员会成员{committee_key} 广播总字节数: {content_to_otherc_total} bytes\n")
    log_file.write(f"委员会门限签名总耗时: {total_signing_time_c:.6f} s\n")
    log_file.write(f"委员会门限签名广播总字节数: {total_committee_broadcast_size} bytes\n")
    tx_in_channel.script_sig = Script([0] + sig_c + [redeem_script.to_hex()])
    content_tor = {"sig_c": sig_c}
    content_tor_json = json.dumps(content_tor)
    content_tor_size = len(content_tor_json.encode('utf-8'))
    log_file.write(f"委员会发给接收方的总字节数: {content_tor_size} bytes\n")
    # print(tx)
    # log_file.write(f"十六进制交易数据为: {tx.serialize()}\n")

    total_size += content_tocr_size_total + content_rtoc_size_total + total_committee_broadcast_size + content_tor_size
    total_time += creation_time + signing_time_s + signing_time_r + total_signing_time_c

    return total_size, total_time, distribution, tx


def update_distribution(distribution: Dict[str, float], payer: str, payments: Dict[str, float]) -> Dict[str, float]:
    new_distribution = distribution.copy()
    total_payment = sum(payments.values()) * SATOSHIS_PER_BTC
    if new_distribution[payer] < total_payment:
        raise ValueError("支付用户的余额不足")
    new_distribution[payer] -= total_payment
    for payee, amount in payments.items():
        new_distribution[payee] += amount * SATOSHIS_PER_BTC
    return new_distribution


def hash256(hexstring: str) -> str:
    data = binascii.unhexlify(hexstring)
    h1 = hashlib.sha256(data)
    h2 = hashlib.sha256(h1.digest())
    return h2.hexdigest()


if __name__ == "__main__":
    user_counts = [6, 12, 24, 48, 96]  #
    committee_num = 3
    committee_threshold = 2
    for user_num in user_counts:
        print(f"测试用户数量: {user_num}，委员会数量： {committee_num}，委员会门限： {committee_threshold}。")
        main(user_num, committee_num, committee_threshold)
