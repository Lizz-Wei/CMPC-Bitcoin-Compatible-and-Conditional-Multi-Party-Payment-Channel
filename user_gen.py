import json
from bitcoinutils.keys import PrivateKey, P2pkhAddress
import requests

from MPC import init

init.initNetwork()

# RPC connection configuration
rpc_user = "rpcuser"
rpc_password = "rpcpassword"
rpc_host = "localhost"
rpc_port = "18443"

# RPC URL
url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}"

# Headers for HTTP request
headers = {
    "Content-Type": "application/json"
}

users = {}
wallet_names = []
for key in ["A", "B", "C"]:
    for i in range(1, 33):
        wallet_names.append((key + str(i)))


def main():
    for name in wallet_names:
        # 生成一个新的私钥
        private_key = PrivateKey()
        # 从私钥获取公钥
        public_key = private_key.get_public_key()
        # 从公钥生成 P2PKH 地址
        address = P2pkhAddress(public_key.get_address().to_string())
        # 为每个用户创建钱包
        response = rpc_command("createwallet", [name])
        if "error" in response:
            print(f"Failed to create wallet {name}: {response['error']}")
        else:
            print(f"Wallet {name} created successfully.")
        # 将地址导入用户钱包
        res = rpc_command("importaddress", [address.to_string(), "", False], name)
        print(res)
        # 存储用户信息
        users[name] = {
            "address": address.to_string(),
            "private_key": private_key.to_wif(),
            "public_key": public_key.to_hex()
        }
        print(
            f"{name} - Address: {users[name]['address']}, Private Key: {users[name]['private_key']}, Public Key: {users[name]['public_key']}")
    # 调用函数生成奖励
    rewards = generate_rewards(users)
    print(rewards)


def rpc_command(method, params=[], wallet_name=None):
    wallet_url = url
    if wallet_name is not None:
        wallet_url += f"/wallet/{wallet_name}"

    payload = {
        "jsonrpc": "1.0",
        "id": "python_script",
        "method": method,
        "params": params
    }
    response = requests.post(wallet_url, headers=headers, data=json.dumps(payload))
    return response.json()


def generate_rewards(users):
    print("正在生成区块获取奖励")
    for user, addr_info in users.items():
        rpc_command('generatetoaddress', [1, addr_info['address']])
    # 用一个地址接受100个确认区块
    print("正在生成100确认区块接收地址")
    # 生成一个新的私钥
    private_key = PrivateKey()
    # 从私钥获取公钥
    public_key = private_key.get_public_key()
    # 从公钥生成 P2PKH 地址
    address = P2pkhAddress(public_key.get_address().to_string())
    rpc_command('generatetoaddress', [100, address.to_string()])
    print("正在获取UTXO")
    for user, addr_info in users.items():
        utxos = rpc_command("listunspent", [0, 9999999, [addr_info['address']], True], user)
        users[user]['utxos'] = utxos['result']
    # 将用户数据写入到users.txt文件中
    with open("users_96.txt", "w") as f:
        json.dump(users, f, indent=4)
    return users


if __name__ == "__main__":
    main()
