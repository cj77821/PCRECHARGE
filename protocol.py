# Test starts here

from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence
from bitcoinutils.keys import PrivateKey
from bitcoinutils.constants import TYPE_RELATIVE_TIMELOCK, TYPE_ABSOLUTE_TIMELOCK

from bitcoinutils.script import Script
from examples.node_proxy import send
from constants import fee
import constants

abs_blocks = 2099051
relative_blocks = 1
relString = 'OP_CHECKSEQUENCEVERIFY'
absString = 'OP_CHECKLOCKTIMEVERIFY'
recharge_coins = 0.00001
e = 0.00001
setup("testnet")
privateA = PrivateKey(constants.private1)
privateB = PrivateKey(constants.private2)
publicA = privateA.get_public_key()
publicB = privateB.get_public_key()


# p2pkh->p2wpkh
# p2wpkhAddress=PrivateKey(privateA).get_publicKey().getP2WPKHAddress()
def fromP2PKHToP2WPKH(txInid, inputIndex, totalAmount, privateA, publicB):
    txIn = TxInput(txInid, inputIndex)
    # preTx = getProxy().gettxout(txInid, inputIndex)
    # totalAmount = float(preTx['value'])

    transactionFee = fee
    remainCoins = totalAmount - transactionFee
    if remainCoins < 0:
        raise ValueError("not enough balance")
    txOut = TxOutput(to_satoshis(remainCoins), publicB.get_segwit_address().to_script_pub_key())
    tx = Transaction([txIn], [txOut])

    script_in = Script(['OP_DUP', 'OP_HASH160', privateA.get_public_key().to_hash160(),
                        'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    sig = privateA.sign_input(tx, 0, script_in)
    print(len(sig))
    txIn.script_sig = Script([sig, privateA.get_public_key().to_hex()])
    return tx

def genTxOn(txInid, inputIndex, totalAmount, coins, publicA, e, publicB, sendBackAddress):

    currentFee = fee
    txIn = TxInput(txInid, inputIndex)
    # preTx = getProxy().gettxout(txInid, inputIndex)
    # totalAmount = float(preTx['value'])
    remainCoins = totalAmount - coins - e - currentFee
    txOut1 = TxOutput(to_satoshis(coins), publicA.get_segwit_address().to_script_pub_key())
    txOut2 = TxOutput(to_satoshis(e), publicB.get_segwit_address().to_script_pub_key())
    txOut3 = TxOutput(to_satoshis(remainCoins), sendBackAddress.get_segwit_address().to_script_pub_key())
    tx = Transaction([txIn], [txOut1, txOut2, txOut3], has_segwit=True)
    return tx


def signTxOn(txOn, privateA, coins):
    script_in = Script(['OP_DUP', 'OP_HASH160', privateA.get_public_key().to_hash160(),
                        'OP_EQUALVERIFY', 'OP_CHECKSIG'])
    amount = coins
    sig = privateA.sign_segwit_input(txOn, 0, script_in, to_satoshis(amount))
    print(len(sig))
    txOn.witnesses.append(Script([sig, privateA.get_public_key().to_hex()]))
    return txOn


def genTxImState(txChannelid, channelAmount, coin1, publicA, coin2, publicB, coin3):
    txIn = TxInput(txChannelid, 0)
    transactionFee = fee
    if coin1 + coin2 + coin3 > channelAmount - transactionFee:
        raise ValueError("not enough balance")
    seqRe = Sequence(TYPE_RELATIVE_TIMELOCK, relative_blocks)
    seqAbs = Sequence(TYPE_ABSOLUTE_TIMELOCK, abs_blocks)
    txOut1 = TxOutput(to_satoshis(coin1), publicA.get_segwit_address().to_script_pub_key())
    txOut2 = TxOutput(to_satoshis(coin2), publicB.get_segwit_address().to_script_pub_key())
    # script_out3 = Script([10000, 'OP_EQUAL', 'OP_IF', seqRe.for_script(), relString, 'OP_DROP', 'OP_2',
    #                       publicA.to_hex(), publicB.to_hex(), 'OP_2', 'OP_CHECKMULTISIG', 'OP_ELSE',
    #                       seqAbs.for_script(), absString,
    #                       'OP_DROP', 'OP_DUP', 'OP_HASH160', publicB.to_hash160(), 'OP_EQUALVERIFY',
    #                       'OP_CHECKSIG', 'OP_ENDIF'])
    script_out3 = Script([10000, 'OP_EQUAL','OP_IF', 'OP_2',
                          publicA.to_hex(), publicB.to_hex(), 'OP_2', 'OP_CHECKMULTISIG', 'OP_ELSE',
                          seqAbs.for_script(), absString,
                          'OP_DROP', 'OP_DUP', 'OP_HASH160', publicB.to_hash160(), 'OP_EQUALVERIFY',
                          'OP_CHECKSIG', 'OP_ENDIF'])
    txOut3 = TxOutput(to_satoshis(coin3), script_out3.to_p2wsh_script_pub_key())
    tx = Transaction([txIn], [txOut1, txOut2, txOut3], has_segwit=True)
    return tx, script_out3


def signTxImState(txImState, channelAmount, privateA, privateB):
    script_in = Script(['OP_2',
                        privateA.get_public_key().to_hex(), privateB.get_public_key().to_hex(), 'OP_2',
                        'OP_CHECKMULTISIG'])

    sig1 = privateA.sign_segwit_input(txImState, 0, script_in, to_satoshis(channelAmount))
    sig2 = privateB.sign_segwit_input(txImState, 0, script_in, to_satoshis(channelAmount))
    txImState.witnesses.append(Script(['OP_0', sig1, sig2, script_in.to_hex()]))
    return txImState




def genTxPay(txOnId, onIndex, coin_on, txStateId, stateIndex, recharge_coins, sendBackAddress):
    # changeAddress: an address where extra coins are sent back to
    transactionFee = fee
    seqRe = Sequence(TYPE_ABSOLUTE_TIMELOCK, relative_blocks)
    txin1 = TxInput(txOnId, onIndex, sequence=seqRe.for_input_sequence())
    txin2 = TxInput(txStateId, stateIndex, sequence=seqRe.for_input_sequence())
    remainCoins = coin_on + recharge_coins - transactionFee
    txOut = TxOutput(to_satoshis(remainCoins), sendBackAddress.get_segwit_address().to_script_pub_key())
    txPay = Transaction([txin1, txin2], [txOut], has_segwit=True)
    return txPay


#     script_in1 = ['OP_DUP', 'OP_HASH160', priv0.get_public_key().to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])
def signTxPay(txPay, coin_on, script_im, coin_im, privateA, privateB):
    script_on = Script(['OP_DUP', 'OP_HASH160', privateA.get_public_key().to_hash160(),
                        'OP_EQUALVERIFY', 'OP_CHECKSIG'])
    sig_on = privateA.sign_segwit_input(txPay, 0, script_on, to_satoshis(coin_on))
    sig_im_A = privateA.sign_segwit_input(txPay, 1, script_im, to_satoshis(coin_im))
    sig_im_B = privateB.sign_segwit_input(txPay, 1, script_im, to_satoshis(coin_im))
    txPay.witnesses.append(Script([sig_on, privateA.get_public_key().to_hex()]))
    txPay.witnesses.append(Script(['OP_0', sig_im_A, sig_im_B, 10000, script_im.to_hex()]))
    return txPay

# all coins contained in A and B's addresses are sent to the channel
# 全部金币冲入通道中
def openChannel(id, inputIndex, totalAmount, owner, privateA, privateB):
    txInId = id
    # preTx = getProxy().gettxout(txInId, inputIndex)
    # fromAddressCount = float(preTx['value'])
    fromAddressCount = totalAmount
    transactionFee = fee
    txIn = TxInput(txInId, inputIndex)
    # PrivateKey().get_public_key().to_hash160()
    p2wsh_witness_script = Script(
        ['OP_2', privateA.get_public_key().to_hex(), privateB.get_public_key().to_hex(), 'OP_2',
         'OP_CHECKMULTISIG'])
    txout = TxOutput(to_satoshis(fromAddressCount - transactionFee), p2wsh_witness_script.to_p2wsh_script_pub_key())
    tx = Transaction([txIn], [txout], has_segwit=True)
    script_code = Script(['OP_DUP', 'OP_HASH160', owner.get_public_key().to_hash160(),
                          'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    sig = owner.sign_segwit_input(tx, 0, script_code, to_satoshis(fromAddressCount))
    tx.witnesses.append(Script([sig, owner.get_public_key().to_hex()]))
    send(tx.serialize())
    print("send success")
    return tx

    # some coins are moved into the channel, and the remaining coins are send back to users.
    # Therefore, compared to openchannel, openchannel2 create a bigger transaction
    # 部分金币冲入通道，其余金币退出各自账户，因此相对于openchannel，openChannel2需要更大的开销
def openChannel2(tx_A, index_A,  totalAmountA, tx_B, index_B, totalAmountB, privateA, privateB, coins):
    txInId = id
    # preTx = getProxy().gettxout(txInId, inputIndex)
    # fromAddressCount = float(preTx['value'])
    transactionFee = fee
    txIn1 = TxInput(tx_A, index_A)
    txIn2 = TxInput(tx_B, index_B)
    PrivateKey().get_public_key().to_hash160()
    p2wsh_witness_script = Script(
        ['OP_2', privateA.get_public_key().to_hex(), privateB.get_public_key().to_hex(), 'OP_2',
         'OP_CHECKMULTISIG'])
    # 多余金币退回A
    txout1 = TxOutput(to_satoshis(totalAmountA - transactionFee/2-coins), privateA.get_public_key().get_segwit_address().to_script_pub_key())
    # 多余金币退回B
    txout2 = TxOutput(to_satoshis(totalAmountB - transactionFee/2 - coins), privateB.get_public_key().get_segwit_address().to_script_pub_key())
    # 开启的通道
    txout3 = TxOutput(to_satoshis(coins *2 ), p2wsh_witness_script.to_p2wsh_script_pub_key())
    tx = Transaction([txIn1, txIn2], [txout1, txout2, txout3], has_segwit=True)
    script_code1 = Script(['OP_DUP', 'OP_HASH160', privateA.get_public_key().to_hash160(),
                          'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    sig1 = privateA.sign_segwit_input(tx, 0, script_code1, to_satoshis(totalAmountA))

    script_code2 = Script(['OP_DUP', 'OP_HASH160', privateB.get_public_key().to_hash160(),
                          'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    sig2 = privateB.sign_segwit_input(tx, 1, script_code2, to_satoshis(totalAmountB))
    tx.witnesses.append(Script([sig1, privateA.get_public_key().to_hex()]))
    tx.witnesses.append(Script([sig2, privateB.get_public_key().to_hex()]))
    send(tx.serialize())
    print("send success")
    return tx


def genAndSignTxState(channelId,index, totalAmount, privateA, coinA, privateB):
    txIn = TxInput(channelId, index)
    transactionFee = fee


    txout1 = TxOutput(to_satoshis(coinA),
                      privateA.get_public_key().get_segwit_address().to_script_pub_key())
    # 多余金币退回B
    txout2 = TxOutput(to_satoshis(totalAmount-fee-coinA),
                      privateB.get_public_key().get_segwit_address().to_script_pub_key())

    txState = Transaction([txIn], [txout1, txout2], has_segwit=True)
    script_in = Script(['OP_2',
                        privateA.get_public_key().to_hex(), privateB.get_public_key().to_hex(), 'OP_2',
                        'OP_CHECKMULTISIG'])
    sig1 = privateA.sign_segwit_input(txState, 0, script_in, to_satoshis(totalAmount))
    sig2 = privateB.sign_segwit_input(txState, 0, script_in, to_satoshis(totalAmount))
    txState.witnesses.append(Script(['OP_0', sig1, sig2, script_in.to_hex()]))
    return txState


def closeChannel(txChannel):
    send(txChannel.serialize())


def updateChannelStatus(txChannelId, totalAmount, coins2A, privateA, coins2B, privateB):
    # preTx = getProxy().gettxout(txChannelId, 0)
    # totalAmount = float(preTx['value'])
    transactionFee = fee
    if totalAmount - transactionFee < coins2A + coins2B:
        raise ValueError("余额不足")
    script = Script(
        ['OP_2', privateA.get_public_key().to_hex(), privateB.get_public_key().to_hex(), 'OP_2',
         'OP_CHECKMULTISIG'])
    txIn = TxInput(txChannelId, 0)
    PrivateKey()
    txOut1 = TxOutput(to_satoshis(coins2A), privateA.get_public_key().get_segwit_address().to_script_pub_key())
    txOut2 = TxOutput(to_satoshis(coins2B), privateB.get_public_key().get_segwit_address().to_script_pub_key())
    tx = Transaction([txIn], [txOut1, txOut2], has_segwit=True)
    print(len(tx.serialize()))
    sig_A = privateA.sign_segwit_input(tx, 0, script, to_satoshis(totalAmount))
    print(len(sig_A))
    sig_B = privateB.sign_segwit_input(tx, 0, script, to_satoshis(totalAmount))
    tx.witnesses.append(Script(['OP_0', sig_A, sig_B, script.to_hex()]))
    print(len(tx.serialize()))
    return tx

def genAndSignRefund(txImstateId, inputIndex, coins, privateA, script):
    seqRe = Sequence(TYPE_RELATIVE_TIMELOCK, 0)
    seqAbs = Sequence(TYPE_ABSOLUTE_TIMELOCK, abs_blocks)
    txIn = TxInput(txImstateId, inputIndex, sequence=seqRe.for_input_sequence())
    transactionFee = fee
    txOut = TxOutput(to_satoshis(coins-transactionFee), privateA.get_public_key().get_segwit_address().to_script_pub_key())
    tx = Transaction([txIn], [txOut], has_segwit=True, locktime=seqAbs.for_input_sequence())
    sig = privateA.sign_segwit_input(tx, 0, script, to_satoshis(coins), )
    tx.witnesses.append(Script([sig, privateA.get_public_key().to_hex(), script.to_hex()]))
    return tx

if __name__ == '__main__':
    transactionFee = fee

    #########           switch p2pkh->p2wpkh        #########  #94
    ######### txId = "7347917cce33b250dde1247db09a6c30cc756a787d7ab99b743818ec4762bf8e"
    # txId = "8625f2f57f191d693bcf76d24630f22238ebf6b478fed10cdbde12f8b63de958"
    # inputIndex = 1
    # tx = fromP2PKHToP2WPKH(txId, inputIndex, 0.00099856, privateA, publicA)
    # send(tx.serialize())
    ##########          genTxOn       ###########   # 253, 144
    # txId = "3af13f3df8847506fc2e9196044d6cf89a22d28df728a00a5a9fdda2510fa3c7"
    # inputIndex = 0
    # totalAmount = 0.00100000
    # txOn = genTxOn(txId, inputIndex, totalAmount, recharge_coins, publicA, e, publicB, publicA)
    # print(len(txOn.serialize()))
    # ##### signTxOn
    # tx = signTxOn(txOn, privateA, totalAmount)
    # print(len(tx.serialize()))
    #
    # send(tx.serialize())

    ##########          openChannel (require p2wpkh on privateA)       ###########  #203
    ##### txId = "75292a819a8c2a85a7adb9e31efe0cbec6bced9e440cee481a7db981405429b7"
    # txId = "aa54859b72d5a99c4006bf81b82f648a8951fc20c62f5d9f9e3e0546a6558f03"
    # inputIndex = 0
    # channel = openChannel(txId, inputIndex, 0.00099556, privateA, privateA, privateB) #
    # print(len(channel.serialize()))
    ##########          updateChannelStatus      ########### #334 test:signed: 334 unsigned:113
    # id = "bb951d56016ca35b280f42af0eb18000731dd18e2ee3400b8070b023915c3ae8"
    # totalAmount = 0.00009256
    # coins2A = 0.00005
    # coins2B = totalAmount - fee -coins2A
    # channelStatus = updateChannelStatus(id, totalAmount,  coins2A, privateA, coins2B, privateB)
    # # send(channelStatus.serialize())
    # print(len(channelStatus.serialize()))

    ##########          generate ImState      ###########   # 376 test:unsigned:156, signed: 376
    # txChannelId = "771a412aa4e3af158bfdeb637602fae3beaa741c904b872c3622c594a8f52f85"
    # channelAmount = 0.00099256
    # coins2A = 0.00039256
    # coins2B = channelAmount - coins2A - transactionFee - recharge_coins
    # txImstate, script = genTxImState(txChannelId, channelAmount, coins2A, publicA, coins2B, publicB, recharge_coins)
    # print(len(txImstate.serialize()))
    # txImstate = signTxImState(txImstate,channelAmount, privateA, privateB)
    # print(len(txImstate.serialize()))
    # send(txImstate.serialize())

    ##########          generate Pay      ###########  #test:unsigned:123 signed:493
    txOnId = "0fb53988bac66e23bf7796fed1b00160544c955530ebe1718c57d3b642d52c43"
    onIndex = 0
    txStateId = "b1791ba3eade125f90c78c187912cdfe2fadec0323b95960196520c9b5f0a99a"
    stateIndex = 2
    txPay = genTxPay(txOnId, onIndex, 0.00099478, txStateId, stateIndex,recharge_coins, publicA)
    print("unsigned:"+ str(len(txPay.serialize())))
    print("unsigned:"+ txPay.get_txid())
    seqRe = Sequence(TYPE_RELATIVE_TIMELOCK, relative_blocks)
    seqAbs = Sequence(TYPE_ABSOLUTE_TIMELOCK, abs_blocks)
    script_im= Script([10000, 'OP_EQUAL','OP_IF', 'OP_2',
                          publicA.to_hex(), publicB.to_hex(), 'OP_2', 'OP_CHECKMULTISIG', 'OP_ELSE',
                          seqAbs.for_script(), absString,
                          'OP_DROP', 'OP_DUP', 'OP_HASH160', publicB.to_hash160(), 'OP_EQUALVERIFY',
                          'OP_CHECKSIG', 'OP_ENDIF'])

    txPay = signTxPay(txPay, 0.00099478, script_im, recharge_coins, privateA, privateB)
    print("signed:"+ str(len(txPay.serialize())))
    print("signed:"+ (txPay.get_txid()))
    send(txPay.serialize())

    ##########          refund   ###########  #test 305
    # seqRe = Sequence(TYPE_RELATIVE_TIMELOCK, relative_blocks)
    # seqAbs = Sequence(TYPE_ABSOLUTE_TIMELOCK, abs_blocks)
    # script_im = Script([10000, 'OP_EQUAL','OP_IF', 'OP_2',
    #                           publicA.to_hex(), publicB.to_hex(), 'OP_2', 'OP_CHECKMULTISIG', 'OP_ELSE',
    #                           seqAbs.for_script(), absString,
    #                           'OP_DROP', 'OP_DUP', 'OP_HASH160', publicB.to_hash160(), 'OP_EQUALVERIFY',
    #                           'OP_CHECKSIG', 'OP_ENDIF'])
    # txImstateId = "495a396faf964e2e3132e43f05f82851567b3ea4e9c6c0f69e16c93e3afbcb8d"
    # inputIndex = 2
    # tx = genAndSignRefund(txImstateId, inputIndex, recharge_coins, privateB, script_im)
    # print(len(tx.serialize()))`
    # send(tx.serialize())

    ##########          Recharge Protocol    ###########
    # e = 0.00001
    #
    # start = time.time()
    # ### create
    # ## genTxOn
    # recharge_coins = 0.00001
    # id = ""
    # inputIndex = 0
    #
    # txOn = genTxOn(id, inputIndex, recharge_coins, publicA, e, publicB, publicB)
    # ## genImstate
    #
    #     #generate a channel state
    # channelId = "54f206172c02d2d65353674798b2d327035b1adc081c993d1ad85303d7104728"
    # channelAmount = 0.00008018
    # coins2A = 0.00005
    # coins2B = channelAmount-coins2A-transactionFee
    # txChannel = updateChannelStatus(channelId, coins2A, privateA, coins2B, privateB)
    #
    #     #update current channel staute
    # txOn = genTxOn(id, inputIndex, 0.01, recharge_coins, publicA, e, publicB, publicB)
    # txOn = signTxOn(txOn, privateA, 0.01)
    # onCreateTime = time.time()
    # print(len(txOn.serialize())) # 444
    ## genImstate
    #
    # # generate a channel state
    # channelId = "54f206172c02d2d65353674798b2d327035b1adc081c993d1ad85303d7104728"
    # channelAmount = 0.00008018
    # coins2A = 0.00005
    # coins2B = channelAmount - coins2A - transactionFee
    # txChannel = updateChannelStatus(channelId, coins2A, privateA, coins2B, privateB)
    #
    # # update current channel state
    # totalAmount = channelAmount
    # coins2A = coins2A
    # coins2B = coins2B - recharge_coins
    # imState, script_im3 = genTxImState(txChannel, coins2A, publicA, coins2B, publicB, recharge_coins)
    #
    # ## generate pay
    # onIndex = 1
    # stateIndex = 3
    # txPay = genTxPay(txOn.get_txid(), onIndex, e, imState,  stateIndex, recharge_coins, publicB)
    #
    # txPay = genTxPay(txOn.get_txid(), onIndex, e, imState, stateIndex, recharge_coins, publicB)
    #
    # ####   sign
    # ### sign txPay
    # txPay = signTxPay()


    #############       open and close    #############
    # open
    # switch to P2WPKH tx_A_id = a150eee25d4d9f2bf88c5f71089b83fe965f75c35e3a42a6f3f01c9c00444dd7, 0.00999700
    # tx_B_id = fc16a01c2ed8c0c0c7b8fdd315309a9dfcf9af0efc42cc82ffc48a9b51d65e3d 0.00099700
    # tx = fromP2PKHToP2WPKH("5b7d4dcdc61cb54b9bf47917bb160aee508818c51797011e36680aed9a8c28b6", 0, 0.00100000, privateB, publicB)
    # send(tx.serialize())

    # openChannel2("a150eee25d4d9f2bf88c5f71089b83fe965f75c35e3a42a6f3f01c9c00444dd7",0, 0.00999700,"fc16a01c2ed8c0c0c7b8fdd315309a9dfcf9af0efc42cc82ffc48a9b51d65e3d",0, 0.00099700, privateA, privateB, 0.0009)
    #  result：ID：4baa0d7908c46bf63738b68e5277ee12c5b5fe89bbba9584d78e8cb99bb768d8， 412B

#     update channel state
#     tx = genAndSignTxState("266433554076a6649f3c6b563b78bcc801b1a19dd54e1ed72e521151ee4b4e0e", 0, 0.00009256, privateA, 0.00004, privateB)
#     #  result：3af13f3df8847506fc2e9196044d6cf89a22d28df728a00a5a9fdda2510fa3c7， 334B

#     closeChannel(tx)
