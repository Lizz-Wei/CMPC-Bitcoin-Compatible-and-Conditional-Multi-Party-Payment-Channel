import bitcoinutils.setup as setup


def initNetwork():
    if setup.get_network() == None: 
        setup.setup('testnet')
