from authproxy import AuthServiceProxy, rpc_connection
import pymongo
import time
from colored import fg, bg, attr
from refreshLine import refreshLine
import sys
from findLastInDb import findLastRecordBlockNumberInMongo

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
color5 = fg("red") + bg(8) + attr("bold")
color6 = fg("blue") + bg(8) + attr("bold")
color6 = fg("white") + bg('red') + attr("bold")
resetColor = attr('reset')

mongoPort = "mongodb://localhost:27200/"

def timeLockInterestRepairInSeedBlocks(correctionArray, block, analyzedSegmentInMemory):
    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]

    for row in correctionArray:
        #print(row['block'], row['txHash'], row['SN'],
        #      row['newInterestAtEnd'], row['newActivatedAmount'])
        blockFromList = row['block']
        txidFromList = row['txHash']
        snFromList = row['SN']
        newIncludedInterest = row['newInterestAtEnd']
        newActivatedAmount = row['newActivatedAmount']
        if blockFromList < block:
            myquery = {"_id": blockFromList}
            target = mycol.find_one(myquery)
            # #(target['_id'])
            #txListFromDb = target['analyzedTxsInBlock']
        else:
            txListFromDb = analyzedSegmentInMemory
        for txFromDb in txListFromDb:

            txHashFromDb = txFromDb['_id']
            if txHashFromDb == txidFromList:
                outputSeg = txFromDb['outputSegment']
                flag = False
                for singleOut in outputSeg:
                    addressFromDb = singleOut['outputAddress']
                    # amountFromDb = singleOut['outputAmount']
                    snFromDb = singleOut['output_n']

                    if snFromDb == snFromList:
                        # print(color2, blockFromList,
                        #      txHashFromDb, snFromDb, resetColor)
                        flag = True
                        initialAmount = singleOut['outputAmount']
                        lockedPeriodInBlocks = singleOut['lockedBlocks']
                        if lockedPeriodInBlocks > 0:
                            multiplier = 262800 / lockedPeriodInBlocks
                            realAnualInterestInSin = multiplier * newIncludedInterest
                            interestRate = round((realAnualInterestInSin *
                                                  100) / initialAmount, 3)
                            #oldActivatedAmount = singleOut['activatedAmount']
                            #oldIncludedInterest = singleOut['interestAtEnd']
                            singleOut['activatedAmount'] = newActivatedAmount
                            singleOut['interestAtEnd'] = newIncludedInterest
                            singleOut['interestRate'] = interestRate
                            singleOut['spentedAtBlock'] = block
                            # singleOut['timeLockActivated'] = 'false'
                            # print(color2, 'new activated amount from ', oldActivatedAmount,
                            #      'to', singleOut['activatedAmount'], resetColor)
                            # print(color2, 'new interest from ', oldIncludedInterest,
                            #      'to', singleOut['interestAtEnd'], resetColor)

                            mycol.update_one({'_id': blockFromList}, {
                                '$set': {'analyzedTxsInBlock': txListFromDb}})
                        else:
                            print('locked period :', lockedPeriodInBlocks)
                            (20)
                if flag == False:
                    print(color4, '---- problem----', resetColor)
    message = 'input segment on current block updated with correct time lock amounts....'
    messageLenght = len(message)
    print(color4,  '-' * messageLenght, resetColor)
    print(color4, message, resetColor)
    print(color4,  '-' * messageLenght, resetColor)


def updateTheSeedUtxoWithZeroInterest(block, txHash, sn, analyzedTxsInOnBuildBlock):
    print('      ', color5, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    print('      ', color5, ' Seed UTXO Updated With ', color3,
          'Zero', color5, ' Interest', resetColor)
    print('      ', color5, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    for row in analyzedTxsInOnBuildBlock:
        tx = row['_id']
        print('-'*100)
        print(tx)
        for inp in row['inputSegment']:
            print(inp)
        print()
        for out in row['outputSegment']:
            print(out)
        print('-'*100)

        print()
    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    myquery = {"_id": block}
    target = mycol.find_one(myquery)
    analyzedTxs = target['analyzedTxsInBlock']
    for singleTx in analyzedTxs:
        tx = singleTx['_id']
        if tx == txHash:
            outputSegment = singleTx['outputSegment']
            for row in outputSegment:
                outputSn = row['output_n']
                if outputSn == sn:
                    amount = row['outputAmount']
                    #row['interestAtEnd'] = 0
                    row['activatedAmount'] = amount
                    row['timeLockActivated'] = 'false'
                    mycol.update_one({'_id': block}, {
                        '$set': {'analyzedTxsInBlock': analyzedTxs}})
    print(color4,  '-----------------------------------------------------------------------', resetColor)
    print(color4, 'Seed block...', block,
          'Seed UTXO updated with zero interest state because timelock failed....', resetColor)
    print(color4,  '-----------------------------------------------------------------------', resetColor)
    return analyzedTxsInOnBuildBlock


def turnUtxoToStxo(spentUtxoList, block):
    lenght = len(spentUtxoList)
    spentUtxoList = neatspentUtxoList(spentUtxoList)

    #print(color6, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # for row in spentUtxoList:
    #    print(row)
    #print(color6, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)

    #print(color6, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    #print(color6, ' Turn the UTXO to STXO Function  ', resetColor)
    #print(color6, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)

    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    totalNumberOfMarkedAsUtxoInthisBlock = 0
    counter = 0
    step = 0
    total = len(spentUtxoList)
    for lineFromList in spentUtxoList:

        #print('lineFromList', lineFromList)
        blockFromList = lineFromList['block']
        #txHashFromList = lineFromList['block']
        myquery = {"height": blockFromList}
        target = mycol.find_one(myquery)

        analyzedTxsFromDb = target['analyzedTxsInBlock']
        txsFromList = lineFromList['txList']
        #print('txsFromList', txsFromList)

        for singleTxFromList in txsFromList:

            #print('singleTxFromList', singleTxFromList)
            txHashFromList = singleTxFromList['tx']
            nFromList = singleTxFromList['n']
            for singleTxFromDb in analyzedTxsFromDb:

                txHashFromDb = singleTxFromDb['_id']

                if txHashFromList == txHashFromDb:
                    totalNumberOfMarkedAsUtxoInthisBlock += 1
                    matchedTx = txHashFromDb
                    outputSegmentOfDb = singleTxFromDb['outputSegment']
                    #listOfNToTurnSpentFromList = singleTxFromList['nEllements']
                    # print('listOfNToTurnSpentFromList',
                    #      listOfNToTurnSpentFromList)
                    # for singleNToTurnSpentFromList in listOfNToTurnSpentFromList:
                    for singleOutputSegmentOfDb in outputSegmentOfDb:
                        nFromDb = singleOutputSegmentOfDb['output_n']
                        if nFromList == nFromDb:
                            matchedN = nFromDb
                            singleOutputSegmentOfDb['state'] = 'STXO'
                            singleOutputSegmentOfDb['spentedAtBlock'] = block
                            # print(color6, 'update the block :',
                            #      blockFromList, 'tx :', matchedTx, 'N', nFromDb)
                            try:
                                singleOutputSegmentOfDb['timeLockActivated'] = 'true'
                            except:
                                continue

            counter += 1
        mycol.update_one({'_id': blockFromList}, {
            '$set': {'analyzedTxsInBlock': analyzedTxsFromDb}})
        if counter % 10 == 0:
            print(color3, 'Updated ', counter, 'of',
                  lenght, 'seed UTXO(s) in ', color6, total, color3, 'block(s)....',   resetColor)
            sys.stdout.write("\033[F")  # Cursor up one line
    print(color3, 'Updated ', counter, 'of',
                  lenght, 'seed UTXO(s) in ', color6, total, color3, 'block(s)....',   resetColor)
    print()

    print(color4,  '--------------------------------------------------------------------------', resetColor)
    print(color4,  'Turn ', color3, totalNumberOfMarkedAsUtxoInthisBlock, color4,
          ' UTXO inputs of current block to STXO in the seed transactions', resetColor)
    print(color4,  '--------------------------------------------------------------------------', resetColor)


def neatspentUtxoList(spentUtxoList):
    uniqueTxArray = []
    uniqueBlockArray = []

    #print(color5, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX      spentUtxoList        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # for row in spentUtxoList:
    #    print(row)
    #print(color5, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)

    for row in spentUtxoList:
        block = row['block']
        if block not in uniqueBlockArray:
            uniqueBlockArray.append(block)

    #print(color1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX      uniqueBlockArray        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # for row in uniqueBlockArray:
    #    print(row)
    #print(color1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # ------------------------------------------------
    txDict = []
    for element in uniqueBlockArray:
        temp = []
        for row in spentUtxoList:
            block = row['block']
            if element == block:
                block = row['block']
                tx = row['tx']
                n = row['n']
                payload = {'block': block, 'tx': tx, 'n': n}
                temp.append(payload)
        txDict.append(temp)

    #print(color3, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX          txDict           XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # for row in txDict:
    #    print(row)
    #print(len(spentUtxoList), ' to ', len(txDict))
    #print(color3, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # ------------------------------------------------------
    returnedArray = []
    for row in txDict:
        tempArray = []
        if len(row) == 1:
            tx = row[0]['tx']
            n = row[0]['n']
            payload = {'tx': tx, 'n': n}
            tempArray.append(payload)
            payload = {'block': row[0]['block'], 'txList': tempArray}
            returnedArray.append(payload)
        else:
            for element in row:
                tx = element['tx']
                n = element['n']
                payload = {'tx': tx, 'n': n}
                tempArray.append(payload)
            payload = {'block': row[0]['block'], 'txList': tempArray}
            returnedArray.append(payload)

    #print(color1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX          Final            XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    # for row in returnedArray:
    #    print(row)
    #print(color1, 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', resetColor)
    return returnedArray


def updateAddressBalanceDb(block, addressesArrayToCalculate):
    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["addressesBalance_V4"]
    #print(color2, '--------------------------------------------------', resetColor)
    for arrayRow in addressesArrayToCalculate:
        #print(color2, arrayRow, resetColor)
        address = arrayRow['address']
        amount = arrayRow['amountInThisBlock']
        myquery = {"_id": address}
        target = mycol.find_one(myquery)
        if target == None:
            #print('New address (', address, ')... created record')
            record = {'_id': address, 'balance': amount,
                      'lastUpdatedInBlock': block}
            mycol.insert_one(record)
        else:
            previusBalance = target['balance']
            newBalance = previusBalance + amount
            mycol.update_many({'_id': address}, {'$set':
                                                 {'balance': newBalance, 'lastUpdatedInBlock': block}})


def addHeightField():
    lastInDb = findLastRecordBlockNumberInMongo()
    myclient = pymongo.MongoClient(mongoPort)
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    for row in range(1, lastInDb, 1):
        id = row
        mycol.update_one({'_id': id}, {'$set': {'height': id}})
        print('height', id)
        sys.stdout.write("\033[F")  # Cursor up one line
