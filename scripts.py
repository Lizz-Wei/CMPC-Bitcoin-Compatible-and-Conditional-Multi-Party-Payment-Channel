from bitcoinutils.script import Script
import init


init.initNetwork()


def get_script_MPCTXs(users, committee_num: int, committee_threshold: int) -> Script:
    # 委员会成员
    committee_keys = list(users.keys())[:committee_num]
    committee_public_keys = [users[key].pk.to_hex() for key in committee_keys]

    # 获取所有用户的公钥
    public_keys = [user.pk.to_hex() for key, user in users.items()]

    # 创建赎回脚本
    script_elements = [2] + public_keys + [len(public_keys), 'OP_CHECKMULTISIG'] \
                      + [committee_threshold] + committee_public_keys + [committee_num, 'OP_CHECKMULTISIG']
    script = Script(script_elements)
    return script
