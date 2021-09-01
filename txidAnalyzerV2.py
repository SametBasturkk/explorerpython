from authproxy import AuthServiceProxy, rpc_connection
import pymongo
import time
from colored import fg, bg, attr

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
resetColor = attr('reset')

mongoPort = "mongodb://localhost:27200/"


def findTheInputAddreses(inputTxid, inputTxidOutput_n, curentBlockTxs, blockNow):

    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    myquery = {"txsInBlock": inputTxid}
    target = mycol.find(myquery)
    try:
        result = target[0]
        block = result['_id']
        target = result['analyzedTxsInBlock']
        # print('tx in block', target)
        for row in target:
            targetTx = row['_id']
            if targetTx == inputTxid:
                tx = targetTx
                outputSegmentOfTx = row['outputSegment']
                for element in outputSegmentOfTx:
                    if element['output_n'] == inputTxidOutput_n:
                        inputCat = element['outputCat']
                        if inputCat == 'checklocktimeverify':
                            inputBlock = block
                            if inputBlock < blockNow:
                                inputAmount = element['activatedAmount']
                                inputAddress = element['outputAddress']
                                timeLockedInterestIncluded = element['interestAtEnd']
                                #print(
                                #    color1, 'input with interest in block :', blockNow, resetColor)
                                # time.sleep(3)
                                return {'address': inputAddress, 'amount': inputAmount, 'interestAmount': timeLockedInterestIncluded, 'block': block, 'tx': tx, 'n': inputTxidOutput_n}

                        else:
                            inputAddress = element['outputAddress']
                            inputAmount = element['outputAmount']
                            return {'address': inputAddress, 'amount': inputAmount, 'block': block, 'tx': tx, 'n': inputTxidOutput_n}
    except:
        print(color3, 'UTXO from the current Block as input', resetColor)
        for line in curentBlockTxs:
            if line['_id'] == inputTxid:
                targetTx2 = line['_id']
                if targetTx2 == inputTxid:
                    outputSegmentOfTx2 = line['outputSegment']
                    for element2 in outputSegmentOfTx2:
                        if element2['output_n'] == inputTxidOutput_n:
                            if element2['outputCat'] == 'checklocktimeverify':
                                print(
                                    color2, 'timelock UTXO from the same block', resetColor)
                                time.sleep(10)
                                inputAddress = element2['outputAddress']
                                inputAmount = element2['outputAmount']
                                timeLockedInterestIncluded = element2['interestAtEnd']
                                return {'address': inputAddress, 'amount': inputAmount, 'interestAmount': timeLockedInterestIncluded,
                                        'block': blockNow, 'tx': targetTx2, 'n': inputTxidOutput_n}
                            else:
                                inputAddress = element2['outputAddress']
                                inputAmount = element2['outputAmount']
                                return {'address': inputAddress, 'amount': inputAmount,
                                        'block': blockNow, 'tx': targetTx2, 'n': inputTxidOutput_n, 'utxoFromCurrentBlock': 'true'}

    print(color4, 'Fail in txidAnalyzer Module', resetColor)
    time.sleep(100)


def txidAnalyzerSeed(txidHash):
    txidOutputList = []
    txidInputList = []
    txidRowFormat = rpc_connection.getrawtransaction(txidHash)
    txidDecoded = rpc_connection.decoderawtransaction(txidRowFormat)
    txidHashSegment = txidDecoded['txid']
#    print('txidHashSegment', txidHashSegment)
    txidVoutSegment = txidDecoded['vout']
    txidVinSegment = txidDecoded['vin']
    return {'vIn': txidVinSegment, 'vOut': txidVoutSegment}


def analyzeInputSegment(tx, n):
    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    myquery = {"TxsInBlock": tx}
    target = mycol.find(myquery)
#    myclient.close()
    fullBlock = target[0]
    print(fullBlock)
    txsInBlock = fullBlock['txsInBlock']
#    print(color1, 'analyze', txsInBlock, resetColor)
    for singleTx in txsInBlock:
        blockNumber = singleTx['includedInBlock']
        if singleTx['TXhash'] == tx:
            outputSegment = singleTx['outputListOfTx']
            for singleOutput in outputSegment:
                if singleOutput['output_n'] == n:
                    address = singleOutput['outputAddress']
                    amount = singleOutput['outputAmount']
                    return blockNumber, address, amount
    print('stopped we have error')


def txidAnalyzer(txidHash, currentBlock):
    txidOutputList = []
    txidInputList = []
    txidRowFormat = rpc_connection.getrawtransaction(txidHash)
    txidDecoded = rpc_connection.decoderawtransaction(txidRowFormat)
    txidHashSegment = txidDecoded['txid']
    txidVoutSegment = txidDecoded['vout']
    txidVinSegment = txidDecoded['vin']
    totalOutputAmmount = 0

    '''
    print(txidHashSegment)
    print()
    print(color3, 'input segment', resetColor)
    for row in txidVinSegment:
        print(row)
    print(color3, 'output segment', resetColor)
    for row in txidVoutSegment:
        print(row)
    time.sleep(10)
    '''

    for singleOutput in txidVoutSegment:
        coinbaseFlag = False
        coinstakeFlag = False
        #print('--------------------------------------------')
        #print (singleOutput)
        scriptPubKeyList = singleOutput['scriptPubKey']
        outputCat = scriptPubKeyList['type']
        #outputAddress = scriptPubKeyList['address']

        if 'coinbase' in str(txidVinSegment):
            coinbaseFlag = True
            outputType = scriptPubKeyList ['type']
            outputCat = 'coinbaseCreation'
            if outputType == 'nulldata' or outputType == 'nonstandard' :
                outputAddress = 'nulldataORnonstandard'
            else :
               outputAddress = scriptPubKeyList['address']
            outputAmountField = singleOutput['value']
            outputAmountField = float("{:.8f}".format(
                float(outputAmountField)))  # convert 0E to decimal
            outputAmount = (outputAmountField)
            output_n = singleOutput['n']
            if output_n == 0:
                creationType = 'minimgReward'
            elif output_n == 1:
                creationType = 'devFee'
            elif outputAmount == 8 or outputAmount == 8:
                creationType = 'miniReward'
            elif outputAmount == 41:
                creationType = 'midReward'
            elif outputAmount == 85:
                creationType = 'bigReward'
            else:
                creationType = 'other'

        elif 'coinstake' in str(txidVinSegment):
            coinstakeFlag = True
            outputType = scriptPubKeyList ['type']
            outputCat = 'coinstakeCreation'
            if outputType == 'nulldata' or outputType == 'nonstandard' :
                outputAddress = 'nulldataORnonstandard'
            else :
                outputAddress = scriptPubKeyList['address']
            outputAmountField = singleOutput['value']
            outputAmountField = float("{:.8f}".format(
                float(outputAmountField)))  # convert 0E to decimal
            outputAmount = (outputAmountField)
            output_n = singleOutput['n']
            #if output_n == 0:
            #    creationType = 'stakeReward'
            #elif output_n == 1:
            #    creationType = 'devFee'
            #elif outputAmount == 8 or outputAmount == 8:
            #    creationType = 'miniReward'
            #elif outputAmount == 41:
            #    creationType = 'midReward'
            #elif outputAmount == 85:
            #    creationType = 'bigReward'
            #else:
            #    creationType = 'other'

            if output_n == 0:
                creationType = 'validationData'
            elif output_n == 1:
                creationType = 'stakeReward'
            elif output_n == 2:
                creationType = 'devFee'
            elif outputAmount == 8 or outputAmount == 8:
                creationType = 'miniReward'
            elif outputAmount == 41:
                creationType = 'midReward'
            elif outputAmount == 85:
                creationType = 'bigReward'
            else:
                creationType = 'other'

        elif outputCat == 'nulldata' and coinbaseFlag is False and coinstakeFlag is False:
            outputAmount = 0
            outputAddress = 'nulldata'
            output_n = 0
            endLockBlock = 'empty'
            lockedPeriodInDays = 'empty'
            interestForThisPeriodInSIN = 0
            lockedPeriodInBlocks = 0

        elif outputCat == 'checklocktimeverify':
            createTimeLOckOutputFlag = True
            outputAddress = scriptPubKeyList['addresses'][0]
            outputAmountField = singleOutput['value']
            outputAmount = outputAmountField
            outputAmount = float("{:.8f}".format(
                float(outputAmountField)))
            output_n = singleOutput['n']
            asm = singleOutput['scriptPubKey']['asm']
            asm = asm.split(' ')
            endLockBlock = int(asm[0])
            if endLockBlock <= currentBlock:
                print(color4, 'Negative period in block ....', resetColor)
                print(color4, 'block Now ....', currentBlock, resetColor)
                print(color4, 'End lock block ....', endLockBlock, resetColor)
                print(color3, 'Fail to create time Lock ....', resetColor)
                createTimeLOckOutputFlag = False
                lockedPeriodInBlocks = endLockBlock - currentBlock
                lockedPeriodInDays = (lockedPeriodInBlocks/720)
                time.sleep(10)

            elif endLockBlock > currentBlock:

                InitialAmount = outputAmount
                lockedPeriodInBlocks = endLockBlock - currentBlock
                lockedPeriodInDays = (lockedPeriodInBlocks/720)
                if currentBlock <= 62520:
                    percentageBlockInterest = 31.34405398 / \
                        262800  # 31.392282346877142857142857142857% Anual first try   | 31.521053983470953844849216364517 2d try \
                    # | 31.501053983470953844849216364517 3d try | 31.451053983470953844849216364517 4d | 31.411053983470953844849216364517 5d \
                    # 31.351053983470953844849216364517 6d | 31.341053983470953844849216364517 7d
                else:
                    percentageBlockInterest = 6.26726873

                percentageInterestForThisPeriod = (
                    lockedPeriodInBlocks * percentageBlockInterest)
                interestForThisPeriodInSIN = (
                    (percentageInterestForThisPeriod/100) * InitialAmount)
                totalAmountAfterPeriod = InitialAmount + interestForThisPeriodInSIN

        else:
            if coinbaseFlag is False and coinstakeFlag is False :
                outputType = scriptPubKeyList ['type']
                if outputType == 'nulldata' or outputType == 'nonstandard' :
                    outputAddress = 'nulldataORnonstandard'
                    endLockBlock = 'empty'
                    output_n = singleOutput['n']
                    lockedPeriodInDays = 'empty'
                    interestForThisPeriodInSIN = 0
                    lockedPeriodInBlocks = 0
                    outputAmount = 0
                else :
                    outputAddress = scriptPubKeyList['address']
                    

                    outputAmountField = singleOutput['value']
                    outputAmountField = float("{:.8f}".format(
                        float(outputAmountField)))  # convert 0E to decimal
                    outputAmount = (outputAmountField)
                    endLockBlock = 'empty'
                    output_n = singleOutput['n']
                    lockedPeriodInDays = 'empty'
                    interestForThisPeriodInSIN = 0
                    lockedPeriodInBlocks = 0

        if outputCat == 'coinstakeCreation':
            #print (color3 , 'record in txidAnalyzer as >>> coinbaseCreation' , resetColor)
            output = {'outputCat': outputCat, 'creationType': creationType, 'outputAddress': outputAddress,
                      'outputAmount': outputAmount, 'output_n': output_n, 'state': 'UTXO'}

        elif outputCat == 'coinbaseCreation':
            #print (color3 , 'record in txidAnalyzer as >>> coinbaseCreation' , resetColor)
            output = {'outputCat': outputCat, 'creationType': creationType, 'outputAddress': outputAddress,
                      'outputAmount': outputAmount, 'output_n': output_n, 'state': 'UTXO'}

        elif outputCat == 'checklocktimeverify' and createTimeLOckOutputFlag is True:
            #print (color3 , 'record in txidAnalyzer as >>> checklocktimeverify' , resetColor)
            output = {'outputCat': outputCat, 'outputAddress': outputAddress,
                      'outputAmount': outputAmount, 'output_n': output_n,  'interestActivatedInBlock': endLockBlock,
                      'lockedBlocks': lockedPeriodInBlocks, 'lockedDays': lockedPeriodInDays,
                      'interestAtEnd': interestForThisPeriodInSIN, 'activatedAmount': totalAmountAfterPeriod, 'timeLockActivated': 'unspecified', 'state': 'UTXO'}

        elif outputCat == 'checklocktimeverify' and createTimeLOckOutputFlag is False:
            #print (color3 , 'record in txidAnalyzer as >>> checklocktimeverify' , resetColor)
            createTimeLOckOutputFlag = True
            output = {'outputCat': outputCat, 'outputAddress': outputAddress,
                      'outputAmount': outputAmount, 'output_n': output_n,  'interestActivatedInBlock': endLockBlock,
                      'lockedBlocks': lockedPeriodInBlocks, 'lockedDays': lockedPeriodInDays,
                      'interestAtEnd': 0, 'activatedAmount': outputAmount, 'negativeLockPeriod': 'True', 'state': 'UTXO'}

        else:
            if coinbaseFlag is False:
                #print (color3 , 'record in txidAnalyzer as >>> last' , resetColor)
                output = {'outputCat': outputCat, 'outputAddress': outputAddress,
                          'outputAmount': outputAmount, 'output_n': output_n, 'state': 'UTXO'}
        txidOutputList.append(output)
        totalOutputAmmount += outputAmount

        totalOutputAmmount = round(totalOutputAmmount, 8)

    #     ++++++ input Segment ++++++++

    if 'coinbase' in str(txidVinSegment):
        payload = 'coinbase'
        txidInputList.append(payload)
        payload = ()
    elif 'coinstake' in str(txidVinSegment):
        payload = 'coinstake'
        txidInputList.append(payload)
    else:
        for singleInput in txidVinSegment:
            #print (singleInput)
            #            print(color2, 'block', block, resetColor)
            inputTxid = singleInput['txid']
            inputTxidOutput_n = singleInput['vout']
            input = {'inputTxid': inputTxid,
                     'inputTxidOutput_n': inputTxidOutput_n}
            txidInputList.append(input)
    TX = {'TXhash': txidHash, 'inputListOfTx': txidInputList,
          'outputListOfTx': txidOutputList, 'totalOutputAmmountOfTx': totalOutputAmmount}
    txidInputList = []
    txidOutputList = []
    return TX


# ask = txidAnalyzer(
#    'a6dd58e8998d672c1d4f61dca4ab6a9d3cdaded3bace2d33e0944685a0fbef7e', 7797)
# print(ask)


def txAnalyzedInJsonFormat(txHash):
    classicResult = txidAnalyzer(txHash)
#    print(classicResult)
    txidHashSegment = classicResult['TXhash']
    txidInputList = classicResult['inputListOfTx']
    txidOutputList = classicResult['outputListOfTx']
    totalOutputAmmount = classicResult['totalOutputAmmountOfTx']
    for row in txidInputList:
        if txidInputList[0] != 'coinbase':
            #            print(row)
            tx = row['inputTxid']
            n = row['inputTxidOutput_n']
#            sinAmount = row['outputAmount']
            addresesInInputSegment = findTheInputAddreses(tx, n)
            return txidHashSegment, txidInputList, txidOutputList, totalOutputAmmount
        else:
            return txidHashSegment, txidInputList, txidOutputList, totalOutputAmmount
