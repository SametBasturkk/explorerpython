from datetime import datetime
import time
from txidAnalyzerV2 import txidAnalyzer, findTheInputAddreses
from findBlockHeight import blockHeight
from nodes import nodes
from blockHashByHeight import blockBasicAlementsByBlockHash
# from memoryPool import getMemoryPool
from nodeStatsForBlock import nodeStatsForBlock
import pymongo
from colored import fg, bg, attr
from activeNodesV2 import activeNodesDbUpdater
from updateEllements import timeLockInterestRepairInSeedBlocks, updateTheSeedUtxoWithZeroInterest, turnUtxoToStxo
import sys
from findLastInDb import findLastRecordBlockNumberInMongo
from findPreviousBlockSupply import findPreviusBlockSupply_ActiveUtxos, currentSupplyActiveUtxos

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
color5 = fg(255) + bg(43)
color6 = fg(0) + bg(255)
color7 = fg('yellow') + bg('blue')
color8 = fg('white') + bg('green')
color9 = fg("red") + bg(8) + attr("bold")
color10 = fg("blue") + bg(8) + attr("bold")
color11 = fg("blue") + bg(0) + attr("bold")
color12 = fg("red") + bg('white') + attr("bold")
color13 = fg("white") + bg('red') + attr("bold")
resetColor = attr('reset')

mongoPort = "mongodb://localhost:27200/"


def calculatesForTimeLockTx(txFees, listInputsWithInterest, resolvedInputSegment, TotalInputAmountInThisTx, block, analyzedTxsInOnBuildBlock):

    if txFees < 0 and abs(txFees) > 0.0001:
        totalInterestInTx = 0
        correctionsArray = []
        ff = '{:.8f}'.format(txFees)
        requestedAmountToStabilizeFees = abs(txFees) + 0.0001
        print()
        print('-' * 70)
        print(color4, 'tx Fees now.....................', ff, resetColor)
        print(color3, 'Amount to correct the difference ',
              requestedAmountToStabilizeFees, resetColor)
        for row in listInputsWithInterest:
            interest = row['includedInterest']
            totalInterestInTx += interest

        totalPercentage = 0
        for row in listInputsWithInterest:
            percentage = (
                row['includedInterest']*100) / totalInterestInTx
            row['percentageMultiplier'] = percentage
            totalPercentage += percentage

        # print(totalPercentage)
        myclient = pymongo.MongoClient(mongoPort)
        mydb = myclient["Sin_V4"]
        mycol = mydb["mainChain_V4"]
        for row in listInputsWithInterest:
            multiplier = row['percentageMultiplier']
            searchedBlock = row['block']
            searchedTxHash = row['txHash']
            searchedSN = row['outputSN']
            # print(color10, 'searchedBlock', searchedBlock, 'block', block)
            if searchedBlock < block:
                myquery = {"_id": searchedBlock}
                target = mycol.find_one(myquery)
                analyzedSegment = target['analyzedTxsInBlock']
            else:
                analyzedSegment = analyzedTxsInOnBuildBlock

            for singleTxSegment in analyzedSegment:
                txHashInDb = singleTxSegment['_id']
                if txHashInDb == searchedTxHash:
                    outputSegment = singleTxSegment['outputSegment']
                    for singleOutput in outputSegment:
                        snInDb = singleOutput['output_n']
                        if snInDb == searchedSN:
                            interestAtEndInDb = singleOutput['interestAtEnd']
                            activatedAmountInDb = singleOutput['activatedAmount']
                            amountToCorrection = (
                                requestedAmountToStabilizeFees * multiplier) / 100
                            # singleOutput ['interestAtEnd'] += amountToCorrection
                            # singleOutput ['activatedAmount'] += amountToCorrection
                            newInterestAtEnd = interestAtEndInDb + amountToCorrection
                            newActivatedAmount = activatedAmountInDb + amountToCorrection
                            payload = {'block': searchedBlock, 'txHash': searchedTxHash, 'SN': searchedSN,
                                       'newInterestAtEnd': newInterestAtEnd, 'newActivatedAmount': newActivatedAmount, }
                            correctionsArray.append(payload)
        for element in correctionsArray:
            blockInArray = element['block']
            txHashInArray = element['txHash']
            snInArray = element['SN']
            newInterestInArray = element['newInterestAtEnd']
            newActivatedAmountInArray = element['newActivatedAmount']
            for row in resolvedInputSegment:
                rowBlock = row['block']
                rowTxHash = row['txHash']
                rowSn = row['outputSN']
                if blockInArray == rowBlock and txHashInArray == rowTxHash and snInArray == rowSn:
                    row['includedInterest'] = round(newInterestInArray, 8)
                    row['amount'] = round(newActivatedAmountInArray, 8)
        for row in resolvedInputSegment:
            try:
                dd = row['includedInterest']
                # print(color3, row, resetColor)
            except:
                continue
        timeLockInterestRepairInSeedBlocks(
            correctionsArray, block, analyzedSegment)
        print('-' * 70)
        print()
        return {'txFees': 0.0001, 'resolvedInputSegment': resolvedInputSegment}

    if txFees >= 0.02:
        print()
        print('-' * 70)
        print(color6, 'txFees --->', txFees,
              'Needs to remove interest from input', resetColor)
        # print('--------------------')
        # need progress to find the most importand from list  ****************************************************
        newFees = 100000
        for singleRecord in listInputsWithInterest:
            blockSeed = singleRecord['block']
            txHash = singleRecord['txHash']
            sn = singleRecord['outputSN']
            includedInterest = singleRecord['includedInterest']
            address = singleRecord['address']
            if txFees-includedInterest < 0:
                continue

            tempFees = txFees-includedInterest
            if (tempFees < newFees and tempFees > 0) and tempFees != txFees:
                print(color1, tempFees, '<', newFees, resetColor)
                deeperTempFees = '{:.8f}'.format(tempFees)
                print(color3, 'find lower fee ...',
                      deeperTempFees, resetColor)
                newFees = tempFees
                targetTxHash = txHash
                targetSn = sn
        if newFees != 100000:
            print(color4, 'the lowest fee--->', deeperTempFees, resetColor)
            for row in resolvedInputSegment:
                txId = row['txHash']
                n = row['outputSN']
                amount = row['amount']
                if txId == targetTxHash and n == targetSn:
                    markedTxid = txId
                    markedN = n
                    amount = row['amount']
                    interest = row['includedInterest']
                    newAmount = amount - interest
                    row['amount'] = newAmount
                    finalTxFees = '{:.8f}'.format(newFees)
                    row['includedInterest'] = 0
                    row['timeLockActivated'] = 'false'
                    print(blockSeed, txHash, sn)
                    repair = updateTheSeedUtxoWithZeroInterest(
                        blockSeed, txHash, sn, analyzedTxsInOnBuildBlock)
                    analyzedTxsInOnBuildBlock = repair[0]
                    break
            for row in resolvedInputSegment:
                txId = row['txHash']
                n = row['outputSN']
                if txId == markedTxid and n == markedN:
                    print(color2, row, 'changed ....', resetColor)
                else:
                    print(color5, row,  resetColor)
            print(color3, 'New Tx Fees :',
                  finalTxFees, resetColor)
            print()
            return {'txFees': newFees, 'resolvedInputSegment': resolvedInputSegment}
        else:
            print(color7, 'tx Fees now.....................',
                  color5,  txFees, resetColor)
            totalInterestInTx = 0
            correctionsArray = []
            ff = '{:.8f}'.format(txFees)
            requestedAmountToStabilizeFees = abs(txFees) - 0.0001
            corrector = '{:.8f}'.format(requestedAmountToStabilizeFees)
            print()
            print('-' * 100)
            print(color4, 'tx Fees now --->', color7, ff, resetColor)
            print(color3, 'Amount to correct the difference ',
                  corrector, resetColor)
            for row in listInputsWithInterest:
                interest = row['includedInterest']
                totalInterestInTx += interest
                print(color6, row, resetColor)
            totalPercentage = 0

            for row in listInputsWithInterest:
                zeroUtxoSeedFlag = False
                if row['includedInterest'] == 0:
                    zeroUtxoSeedFlag = True
                    continue
                else:
                    percentage = (
                        row['includedInterest']*100) / totalInterestInTx
                    row['percentageMultiplier'] = percentage
                    totalPercentage += percentage
                    print(color6, row, resetColor)

            myclient = pymongo.MongoClient(mongoPort)
            mydb = myclient["Sin_V4"]
            mycol = mydb["mainChain_V4"]
            for row in listInputsWithInterest:
                if zeroUtxoSeedFlag is True:
                    print(
                        color4, 'cant go lower the fee with this , because this UTXO have zero interest....', resetColor)
                    period = 5
                    for seg in range(1, period, 1):
                        print(
                            color12, 'hold the old fees at this time....', resetColor)
                        time.sleep(1)
                        sys.stdout.write("\033[F")  # Cursor up one line
                        print(
                            color13, 'hold the old fees at this time....', resetColor)
                        time.sleep(1)
                        sys.stdout.write("\033[F")  # Cursor up one line
                    print()

                    holdOldFee = txFees
                    continue
                else:

                    multiplier = row['percentageMultiplier']
                    searchedBlock = row['block']
                    searchedTxHash = row['txHash']
                    searchedSN = row['outputSN']
                    myquery = {"_id": searchedBlock}
                    target = mycol.find_one(myquery)
                    try:
                        analyzedSegment = target['analyzedTxsInBlock']
                    except:
                        print(
                            color3, 'this tx is in curent calculated block', resetColor)
                        analyzedSegment = analyzedTxsInOnBuildBlock

                    for singleTxSegment in analyzedSegment:
                        txHashInDb = singleTxSegment['_id']
                        if txHashInDb == searchedTxHash:
                            outputSegment = singleTxSegment['outputSegment']
                            for singleOutput in outputSegment:
                                snInDb = singleOutput['output_n']
                                if snInDb == searchedSN:

                                    interestAtEndInDb = singleOutput['interestAtEnd']
                                    activatedAmountInDb = singleOutput['activatedAmount']
                                    amountToCorrection = (
                                        requestedAmountToStabilizeFees * multiplier) / 100

                                    # singleOutput ['interestAtEnd'] += amountToCorrection
                                    # singleOutput ['activatedAmount'] += amountToCorrection
                                    newInterestAtEnd = interestAtEndInDb - amountToCorrection
                                    newActivatedAmount = activatedAmountInDb - amountToCorrection
                                    payload = {'block': searchedBlock, 'txHash': searchedTxHash, 'SN': searchedSN,
                                               'newInterestAtEnd': newInterestAtEnd, 'newActivatedAmount': newActivatedAmount, }
                                    correctionsArray.append(payload)
            for element in correctionsArray:
                blockInArray = element['block']
                txHashInArray = element['txHash']
                snInArray = element['SN']
                newInterestInArray = element['newInterestAtEnd']
                newActivatedAmountInArray = element['newActivatedAmount']
                for row in resolvedInputSegment:
                    rowBlock = row['block']
                    rowTxHash = row['txHash']
                    rowSn = row['outputSN']
                    if blockInArray == rowBlock and txHashInArray == rowTxHash and snInArray == rowSn:
                        row['includedInterest'] = newInterestInArray
                        row['amount'] = newActivatedAmountInArray
            for row in resolvedInputSegment:
                try:
                    dd = row['includedInterest']
                    #print(color3, row, resetColor)
                except:
                    continue
            timeLockInterestRepairInSeedBlocks(
                correctionsArray, block, analyzedTxsInOnBuildBlock)
            print()
            try:
                return {'txFees': holdOldFee, 'resolvedInputSegment': resolvedInputSegment}
            except:
                return {'txFees': 0.0001, 'resolvedInputSegment': resolvedInputSegment}
    else:
        #print(color10, 'Do nothing leave it as it ', resetColor)
        ff = '{:.8f}'.format(txFees)
        # print(color8, 'Returned W/O changes... Fees ---> ',
        #      color3, ff,  resetColor)
        return {'txFees': txFees, 'resolvedInputSegment': resolvedInputSegment}


def unixTimeToUtcDatetime(askedTime):
    utc_time = datetime.utcfromtimestamp(askedTime)
    resolvedUtcDateTime = (utc_time.strftime("%Y-%m-%d %H:%M:%S"))
    resolvedUtcDate = int(str(utc_time.strftime("%Y%m%d")))
    return resolvedUtcDate


def mineData(startBlock, endBlock):
    checkCreatorFlag = False
    startMetrics = time.time()
    timerStart = 0
    for block in range(startBlock, endBlock+1):
        #if block == 2001:
        #    endMetrics = time.time()
        #    duration = int(endMetrics - startMetrics)
        #    print('2000 blocks calculated in :', duration, 'seconds.....')
        #    time.sleep(60)
        counter = 0
        print()
        print('+' * 100)
        print()
        print(color6, 'block :', block, resetColor)
        if timerStart == 0:
            timerStart = int(time.time())
        totalCoinsBurnedInBlock = 0
        totalCoinsCreatedInBlockFromCoinbase = 0
        totalCoinsCreatedInBlockFromTimeLock = 0
        analyzedTxs = []
        addressesInvolvedInThisBlock = []
        createdUtxoInBlock = 0
        removedUtxoInBlock = 0
        createdCoinsInCoinbase = 0
        createdCoinsInCoinstake = 0
        txInBlock = []
        txInBlockList = []
        listOfUtxoInBlockToTurnSpent = []
        if block % 100 == 0:
            timerSEnd = int(time.time())
            duration = timerSEnd - timerStart
            print(color2, 'Last 100(', block-99, '-', block,
                  ')  blocks calculated in :', duration, 'second(s)',  resetColor)
            timerStart = 0
        blockSegments = blockBasicAlementsByBlockHash(block)
        blockHash = blockSegments['blockHash']
        Hash = blockHash['hash']
        confirmations = blockHash['confirmations']
        strippedsize = blockHash['strippedsize']
        size = blockHash['size']
        weight = blockHash['weight']
        version = blockHash['version']
        versionHex = blockHash['versionHex']
        merkleroot = blockHash['merkleroot']
        txInBlock = blockHash['tx']
        nonce = blockHash['nonce']
        bits = blockHash['bits']
        chainwork = blockHash['chainwork']
        nTx = blockHash['nTx']
        diff = blockHash['difficulty']
        difficulty = float("{:.8f}".format(
            float(diff)))  # convert 0E to decimal
        blockTime = blockHash['time']
        mediantime = blockHash['mediantime']
        previousblockhash = blockHash['previousblockhash']
        try:
            nextblockhash = blockHash['nextblockhash']
        except:
            nextblockhash = 'not created yet'
        
        #for singleTx in txInBlock:
        #    print (color11 , singleTx , resetColor)
        #    print()
        #print ('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO')
        txCounter0 = True
        for singleTx in txInBlock:
            
            createdCoinsInThisTx = 0

            burnedInCoinbase = 0
            burnedInCoinstake = 0
            burnedGeneralCoinsInThisTx = 0
            burnedLockRewardCoinsInThisTx = 0
            burnedMetadataCoinsInThisTx = 0
            amountToOtherAddresses = 0
            TotalInputAmountInThisTx = 0
            newCoinsFromTimeLockInThisTx = 0
            resolvedInputSegment = []
            listInputsWithInterest = []
            response = txidAnalyzer(singleTx, block)
            #print (color10 , 'responce' , response , resetColor)

            txHash = response['TXhash']
            vIn = response['inputListOfTx']
            vOut = response['outputListOfTx']
            txOutputAmount = response['totalOutputAmmountOfTx']

            # print(vIn)
            
            for singleTxInInputSegment in vIn:
                #print(color2, singleTxInInputSegment, resetColor)
                if vIn == ['coinbase']:
                    txCat = 'coinbase'
                    #print (color12 , 'inputSegmentincoinbase ' , singleTxInInputSegment , resetColor)
                    
                    # find the new created coins in this block
                    
                    for row in vOut:
                        coinbaseOutputAddress = row['outputAddress']
                        createdAmount = row['outputAmount']
                        createdCoinsInCoinbase += createdAmount
                        #   >>>>>>>>>> check pos or pow create this block
                        if txCounter0 is True :
                            txCounter0 = False

                            if coinbaseOutputAddress == 'nulldataORnonstandard' and checkCreatorFlag is False :
                                blockCreator = 'pos'
                                checkCreatorFlag is True
                                print (color1 , 'pos' , resetColor)
                            elif coinbaseOutputAddress != 'nulldataORnonstandard' and checkCreatorFlag is False :
                                blockCreator = 'pow'
                                checkCreatorFlag is True
                                print (color3 , 'pow' , resetColor)
                            print ('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
                            #else :
                            #    blockCreator = 'pos'
                            #    checkCreatorFlag == True
                        
                        if coinbaseOutputAddress == 'SinBurnAddress123456789SuqaXbx3AMC':
                            burnedInCoinbase += createdAmount
                        payload = {'address': coinbaseOutputAddress,
                                   'tempAmount': createdAmount}
                        addressesInvolvedInThisBlock.append(payload)
                    resolvedInputSegment.append('coinbase')

                elif vIn == ['coinstake']:
                    txCat = 'coinstake'
                    #print (color12 , 'inputSegmentincoinstake ' , singleTxInInputSegment , resetColor)
                    # find the new created coins in this block
                    for row in vOut:
                        coinstakeOutputAddress = row['outputAddress']
                        createdAmount = row['outputAmount']
                        createdCoinsInCoinstake += createdAmount
                        if coinbaseOutputAddress == 'SinBurnAddress123456789SuqaXbx3AMC':
                            burnedInCoinstake += createdAmount
                        payload = {'address': coinstakeOutputAddress,
                                   'tempAmount': createdAmount}
                        addressesInvolvedInThisBlock.append(payload)
                    resolvedInputSegment.append('coinstake')

                else:
                    txCat = 'ordinary'
                    txInVin = singleTxInInputSegment['inputTxid']
                    nInVin = singleTxInInputSegment['inputTxidOutput_n']
                    resolvedData = findTheInputAddreses(
                        txInVin, nInVin, analyzedTxs, block)
                    returnedTxHash = resolvedData['tx']
                    returnedN = resolvedData['n']
                    try:
                        address = resolvedData['address']
                        amount = resolvedData['amount']
                        includedInterest = resolvedData['interestAmount']
                        txsBlock = resolvedData['block']
                        TotalInputAmountInThisTx += amount
                        newCoinsFromTimeLockInThisTx += includedInterest

                        singleInputOnVinSegment = {'block': txsBlock,
                                                   'txHash': txInVin, 'outputSN': nInVin, 'address': address, 'includedInterest': includedInterest,  'amount': amount}
                        listInputsWithInterest.append(singleInputOnVinSegment)
                    except:
                        address = resolvedData['address']
                        amount = resolvedData['amount']
                        txsBlock = resolvedData['block']
                        TotalInputAmountInThisTx += amount
                        singleInputOnVinSegment = {'block': txsBlock,
                                                   'txHash': txInVin, 'outputSN': nInVin, 'address': address, 'amount': amount}
                    payload = {'address': address,
                               'tempAmount': amount * -1}
                    addressesInvolvedInThisBlock.append(payload)
                    resolvedInputSegment.append(singleInputOnVinSegment)
                    payloadForLstOfUtxoInBlockToTurnSpent = {
                        'block': txsBlock, 'tx': returnedTxHash, 'n': returnedN}
                    listOfUtxoInBlockToTurnSpent.append(
                        payloadForLstOfUtxoInBlockToTurnSpent)
                    counter += 1
                if counter % 10 == 0:
                    print(color9, 'Analyze', color2,  counter, color9,
                          'input Tx(s)....',  resetColor)
                    sys.stdout.write("\033[F")  # Cursor up one line

            # print(color1, vOut, resetColor)
            if txCat != 'coinbase' and txCat != 'coinstake':
                #print (color1 , 'vIn' , vIn , resetColor)
                for row in vOut:

                    txCat = 'ordinary'
                    address = row['outputAddress']
                    amount = row['outputAmount']
                    payload = {'address': address,
                               'tempAmount': amount}
                    addressesInvolvedInThisBlock.append(payload)
                    if address == 'SinBurnAddress123456789SuqaXbx3AMC':
                        burnedGeneralCoinsInThisTx += amount
                    elif address == 'SinBurnAddressForLockRewardXTbeffB':
                        burnedLockRewardCoinsInThisTx += amount
                    elif address == 'SinBurnAddressForMetadataXXXXEU2mj':
                        burnedMetadataCoinsInThisTx += amount
                    else:
                        amountToOtherAddresses += amount
                totalInAmount = TotalInputAmountInThisTx
                totalBurned = burnedGeneralCoinsInThisTx + \
                    burnedLockRewardCoinsInThisTx + burnedMetadataCoinsInThisTx
                totalOutAmount = totalBurned + amountToOtherAddresses
                txFees = round(totalInAmount - totalOutAmount, 8)
                request = calculatesForTimeLockTx(
                    txFees, listInputsWithInterest, resolvedInputSegment, TotalInputAmountInThisTx, block, analyzedTxs)

                txFees = request['txFees']
                resolvedInputSegment = request['resolvedInputSegment']

            elif txCat == 'coinbase':
                burnedGeneralCoinsInThisTx = burnedInCoinbase
                burnedLockRewardCoinsInThisTx = 0
                burnedMetadataCoinsInThisTx = 0
                totalBurned = burnedInCoinbase
                totalCreatedAmount = createdCoinsInCoinbase
                txOutputAmount = amountToOtherAddresses
                txFees = 0

            elif txCat == 'coinstake':
                burnedGeneralCoinsInThisTx = burnedInCoinbase
                burnedLockRewardCoinsInThisTx = 0
                burnedMetadataCoinsInThisTx = 0
                totalBurned = burnedInCoinbase
                totalCreatedAmount = createdCoinsInCoinstake
                txOutputAmount = amountToOtherAddresses
                txFees = 0

            if txCat == 'coinbase':
                singleAnalyzedTx = {'_id': singleTx,
                                    'txCat': txCat,
                                    'inputSegment': resolvedInputSegment,
                                    'outputSegment': vOut,
                                    'totalCreatedAmount': totalCreatedAmount,
                                    'coinsCreatedFromCoinbase': createdCoinsInCoinbase,
                                    'burnTo123456789Suqa': burnedGeneralCoinsInThisTx,
                                    'totalBurned': burnedInCoinbase,
                                    'fees': txFees

                                    }
            elif txCat == 'coinstake':
                singleAnalyzedTx = {'_id': singleTx,
                                    'txCat': txCat,
                                    'inputSegment': resolvedInputSegment,
                                    'outputSegment': vOut,
                                    'totalCreatedAmount': totalCreatedAmount,
                                    'coinsCreatedFromCoinstake': createdCoinsInCoinstake,
                                    'burnTo123456789Suqa': burnedGeneralCoinsInThisTx,
                                    'totalBurned': burnedInCoinstake,
                                    'fees': txFees
                                    }
            else:
                if newCoinsFromTimeLockInThisTx > 0:
                    singleAnalyzedTx = {'_id': singleTx,
                                        'txCat': txCat,
                                        'inputSegment': resolvedInputSegment,
                                        'outputSegment': vOut,
                                        'coinsCreatedFromTimeLock': newCoinsFromTimeLockInThisTx,
                                        'burnTo123456789Suqa': burnedGeneralCoinsInThisTx,
                                        'burnToLockReward': burnedLockRewardCoinsInThisTx,
                                        'burnToMetadata': burnedMetadataCoinsInThisTx,
                                        'totalBurned': totalBurned,
                                        'fees': txFees
                                        }
                else:
                    singleAnalyzedTx = {'_id': singleTx,
                                        'txCat': txCat,
                                        'inputSegment': resolvedInputSegment,
                                        'outputSegment': vOut,
                                        'burnTo123456789Suqa': burnedGeneralCoinsInThisTx,
                                        'burnToLockReward': burnedLockRewardCoinsInThisTx,
                                        'burnToMetadata': burnedMetadataCoinsInThisTx,
                                        'totalBurned': totalBurned,
                                        'fees': txFees
                                        }

            analyzedTxs.append(singleAnalyzedTx)

            # myclient = pymongo.MongoClient(mongoPort)
            # mydb = myclient["Sin_V4"]
            # mycol = mydb["tx_db_V3"]
            # mycol.insert_one(payload)
            #  myclient.close()

            totalCoinsBurnedInBlock += totalBurned
            totalCoinsCreatedInBlockFromTimeLock += newCoinsFromTimeLockInThisTx
        print(color9, 'Analyze', color2,  counter, color9,
              'input Tx(s)....',  resetColor)
        sys.stdout.write("\033[F")  # Cursor up one line
        createdUtxoInBlock = 0
        removedUtxoInBlock = 0
        print()

        for singleTx in analyzedTxs:
            #txHash = singleTx['_id']
            txInputSegment = singleTx['inputSegment']
            txOuputSegment = singleTx['outputSegment']

            createdUtxoInBlock += len(txOuputSegment)
            removedUtxoInBlock += len(txInputSegment)

            #     XXX   UTXO  add     XXX
            # for singleTxOut in txOuputSegment:
            #    address = singleTxOut['outputAddress']
            #    sn = str(singleTxOut['output_n'])
            #    id = txHash + '_' + sn + '_' + address
            #    tx = txHash
            #    try:
            #        addrAmount = singleTxOut['activatedAmount']
            #    except:
            #        addrAmount = singleTxOut['outputAmount']
            #    # payload = {'_id': id, 'blockIncluded': block,
            #    #           'txHash': txHash, 'address': address, 'amount': addrAmount}
            #    # mycol.insert_one(payload)
            #    createdUtxoInTx += 1

            #     XXX   UTXO  Remove     XXX
            # for singleTxIn in txInputSegment:
            #    if singleTxIn != 'coinbase':
            ##        rowTxInHash = singleTxIn['txHash']
            #        rowTxInAddress = singleTxIn['address']
            #        sn = str(singleTxIn['outputSN'])
            #        searchedId = rowTxInHash + '_' + sn + '_' + rowTxInAddress
            #        myquery = {"_id": searchedId}
            #        try:
            #            removedUtxoInTx += 1
            #        except:
            #            print(color5, 'cant find in db to remove', resetColor)

            #createdUtxoInBlock += createdUtxoInTx
            #removedUtxoInBlock += removedUtxoInTx

        finalArrayOfUniqueInvolvedAddressWithTotalAmounts = []
        uniqueAddress = []
        for row in addressesInvolvedInThisBlock:
            if row['address'] not in uniqueAddress:
                uniqueAddress.append(row['address'])

        for singleAddress in uniqueAddress:
            tempSum = 0
            for row in addressesInvolvedInThisBlock:
                address = row['address']
                amount = row['tempAmount']
                if singleAddress == address:
                    tempSum += amount
            payload = {'address': singleAddress, 'amountInThisBlock': tempSum}
            finalArrayOfUniqueInvolvedAddressWithTotalAmounts.append(
                payload)

        previusSupplyActiveUtxos = findPreviusBlockSupply_ActiveUtxos(block)
        utxoImpactInThisBlock = createdUtxoInBlock - removedUtxoInBlock

        totalCreatedInBlock = createdCoinsInCoinbase + createdCoinsInCoinstake +\
            totalCoinsCreatedInBlockFromTimeLock
        blockImpactInSupply = totalCreatedInBlock - totalCoinsBurnedInBlock

        supplyAndActiveUtxos = currentSupplyActiveUtxos(
            previusSupplyActiveUtxos, utxoImpactInThisBlock, blockImpactInSupply)
        supply = supplyAndActiveUtxos['supplyInCurrentBlock']
        activeUtxos = supplyAndActiveUtxos['activeUtxoInCurrentBlock']

        myclient = pymongo.MongoClient(mongoPort)
        mydb = myclient["Sin_V4"]
        mycol = mydb["mainChain_V4"]
        if block <= 170000:
            mydict = {"_id": block,
                      'height': block,
                      'blockHash': Hash,
                      'previousBlockHash': previousblockhash,
                      'nextBlockHash': nextblockhash,
                      'confirmations': confirmations,
                      'strippedsize': strippedsize,
                      'size': size,
                      'weight': weight,
                      'version': version,
                      'versionHex': versionHex,
                      'merkleroot': merkleroot,
                      'txsInBlock': txInBlock,
                      'nonce': nonce,
                      'bits': bits,
                      'chainwork': chainwork,
                      'nTx': nTx,
                      'blockCreatorType' : blockCreator,
                      'difficulty': difficulty,
                      'blockTime': blockTime,
                      'calendarUtcStamp': time.asctime(time.gmtime(blockTime)),
                      'dateUtcStampYYYYMMDD': unixTimeToUtcDatetime(blockTime),
                      'mediantime': mediantime,
                      'analyzedTxsInBlock': analyzedTxs,
                      'coinsCreatedFromCoinbase': createdCoinsInCoinbase,
                      'coinsCreatedFromCoinstake': createdCoinsInCoinstake,
                      'coinsCreatedFromTimelock': totalCoinsCreatedInBlockFromTimeLock,
                      'coinsBurnedInBlock': totalCoinsBurnedInBlock,
                      'addressesIvnolvedInBlock': finalArrayOfUniqueInvolvedAddressWithTotalAmounts,
                      'createdUtxoInBlock': createdUtxoInBlock,
                      'removedUtxoInBlock': removedUtxoInBlock,
                      'supplyInCurrentBlock': supply,
                      'activeUtxoInCurrentBlock': activeUtxos
                      }
        else:
            nodesStats = nodes()
            nodesFullMap = nodesStats['fullMapOfAllNodes']
            nodeStats = nodeStatsForBlock(block, nodesFullMap)
            mydict = {"_id": block,
                      'height': block,
                      'blockHash': Hash,
                      'previousBlockHash': previousblockhash,
                      'nextBlockHash': nextblockhash,
                      'confirmations': confirmations,
                      'strippedsize': strippedsize,
                      'size': size,
                      'weight': weight,
                      'version': version,
                      'versionHex': versionHex,
                      'merkleroot': merkleroot,
                      'txsInBlock': txInBlock,
                      'nonce': nonce,
                      'bits': bits,
                      'chainwork': chainwork,
                      'nTx': nTx,
                      'blockCreatorType' : blockCreator,
                      'difficulty': difficulty,
                      'blockTime': blockTime,
                      'calendarUtcStamp': time.asctime(time.gmtime(blockTime)),
                      'dateUtcStampYYYYMMDD': unixTimeToUtcDatetime(blockTime),
                      'mediantime': mediantime,
                      'analyzedTxsInBlock': analyzedTxs,
                      'coinsCreatedFromCoinbase': createdCoinsInCoinbase,
                      'coinsCreatedFromCoinstake': createdCoinsInCoinstake,
                      'coinsCreatedFromTimelock': totalCoinsCreatedInBlockFromTimeLock,
                      'coinsBurnedInBlock': totalCoinsBurnedInBlock,
                      'nodesStats': nodeStats,
                      'addressesIvnolvedInBlock': finalArrayOfUniqueInvolvedAddressWithTotalAmounts,
                      'createdUtxoInBlock': createdUtxoInBlock,
                      'removedUtxoInBlock': removedUtxoInBlock,
                      'supplyInCurrentBlock': supply,
                      'activeUtxoInCurrentBlock': activeUtxos
                      }

        mycol.insert_one(mydict)

        if len(listOfUtxoInBlockToTurnSpent) != 0:
            turnUtxoToStxo(listOfUtxoInBlockToTurnSpent, block)
        else:
            print(color6, 'No entrys in input Segment ...no calculations', resetColor)
        '''
        updateAddressBalanceDb(
            block, finalArrayOfUniqueInvolvedAddressWithTotalAmounts)
        '''
        if endBlock-startBlock < 100:
            print(block)


def fired(blockNumberNow):
    startBlock = findLastRecordBlockNumberInMongo()
    endBlock = blockNumberNow
    #    getMemoryPool()

    print('start update the database from block ',
          startBlock, 'until current block ', endBlock)
    mineData(startBlock, endBlock)


# Main params
block = 0
memoryPoolTxCount = 0
bestHeightInMongo = 0
firstPassFlag = True


while True:
    currentBlock = blockHeight()
    print('block height now in chain: ', currentBlock)
    if firstPassFlag is True:
        print(color4, 'For security reasons the last entrys from all Dbs need to remove', resetColor)
        firstPassFlag = False
    if block != currentBlock:
        print('New block     : ', currentBlock)
        fired(currentBlock)
        block = currentBlock
        #try:
        #    activeNodesDbUpdater()
        #except:
        #    print('crash in node array creation')
        time.sleep(5)
    else:
        time.sleep(5)
