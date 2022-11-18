# Copyright (C) 2018-2020 The python-bitcoin-utils developers
#
# This file is part of python-bitcoin-utils
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of python-bitcoin-utils, including this file, may be copied,
# modified, propagated, or distributed except according to the terms contained
# in the LICENSE file.


from bitcoinutils.setup import setup
from bitcoinutils.proxy import NodeProxy
# ip = '172.20.10.20'
ip = '127.0.0.1'
def getProxy():
    setup('testnet')

    # get a node proxy using default host and port
    proxy = NodeProxy('user', '123', ip,8332).get_proxy()
    return proxy


def send(hexstring):
    # always remember to setup the network
    setup('testnet')

    # get a node proxy using default host and port
    proxy = NodeProxy('user', '123', ip,8332).get_proxy()
    # proxy = NodeProxy('rpcuser', 'rpcpw').get_proxy()

    # call the node's getblockcount JSON-RPC method
    # count = proxy.getblockcount()
    result = proxy.sendrawtransaction(hexstring)
    print("send success")
    # print(count)

    # call the node's getblockhash JSON-RPC method
    # block_hash = proxy.getblockhash(count)


    # call the node's getblock JSON-RPC method and print result
    # block = proxy.getblock(block_hash)
    # print(block)

    # print only the difficulty of the network
    # print(block['difficulty'])

if __name__ == "__main__":
    proxy = getProxy()
    # count = proxy.getlockcount()
    # count = proxy.getblockcount()
    trans = proxy.gettransaction("7347917cce33b250dde1247db09a6c30cc756a787d7ab99b743818ec4762bf8e");

