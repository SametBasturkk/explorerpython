import json
import time
from colored import fg, bg, attr
import pymongo
from findBlockHeight import blockHeight
from addressFullHistoryV2 import addressHistoryV2


def databaseIntegrity():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V3"]
    mycol = mydb["mainChain_V3"]
    target = mycol.find().sort('_id', -1)
    counter = 0
    flag = False
    for row in target:
        counter += 1
        height = row['_id']
        if height == 0:
            return (str(counter) + " block's checked and all is good")
#        print('height', height)
        if flag is False:
            previous = row['previousBlockHash']
            flag = True
            continue
        currentHash = row['blockHash']
        if previous == currentHash:
            previous = row['previousBlockHash']
        else:
            return ' wrong integrity in block :', height
    return (str(counter) + " block's checked and all is good")


def findEllement(dataInput):
    try:
        question = int(dataInput)
    except:
        question = dataInput
    if type(question) == int:
        if question > 0 and question <= last_idInMongo():
            print('in')
            myclient = pymongo.MongoClient("mongodb://localhost:27017/")
            mydb = myclient["Sin_V3"]
            mycol = mydb["mainChain_V3"]
            myquery = {'_id': question}
            target = mycol.find_one(myquery)
            myclient.close()
            if target:  # check if target is empty if yes return it
                return {'session1': 'search_by_Block_number', 'session2': target}
        else:
            return {'session1': 'No block in this range '}
    if len(question) == 64:
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["Sin_V3"]
        mycol = mydb["mainChain_V3"]
        myquery = {'blockHash': question}
        target = mycol.find_one(myquery)
        if target:  # check if target is empty if yes return it
            myclient.close()
            return {'session1': 'search_by_Block_number', 'session2': target}

    if len(question) == 64:
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["Sin_V3"]
        mycol = mydb["tx_db"]
        myquery = {'_id': question}
        target = mycol.find_one(myquery)
        if target:  # check if target is empty if yes return it
            myclient.close()
            return {'session1': 'search_by_Tx_Id', 'session2': target}

    if len(question) == 34:
        body = addressHistoryV2(question)
        return {'session1': 'search_by_Address', 'session2': body}
#   if you are in here no resaults return notFound
    return {'session1': 'notFound'}


def lastBlockInWallet():
    lastBlock = last_idInMongo()
    return {'lastBlock': lastBlock}


def nodeStats():
    lastBlock = last_idInMongo()
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V3"]
    mycol = mydb["mainChain_V3"]
    myquery = {'_id': lastBlock}
    target = mycol.find_one(myquery)
#    print(target)
    nodeStat = target['nodesStat']
    myclient.close()
    return {'blockHeight': lastBlock, 'nodeStats': nodeStat}


def difficulty_txsPerBlockLast200Blocks():
    diffLast1000Blocks = []
    lastBlock = last_idInMongo()
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V3"]
    mycol = mydb["mainChain_V3"]
    for i in range((lastBlock-200), lastBlock+1, 1):
        myquery = {'_id': i}
        target = mycol.find_one(myquery)
        blockNumber = target['_id']
        difficulty = target['difficulty']
        txPerBlock = target['nTx']
#        lenTxPerBlock = len(txPerBlock)
        data = {'block_number': blockNumber,
                'block_difficulty': difficulty, 'txsPerBlock': txPerBlock}
        diffLast1000Blocks.append(data)
    myclient.close()
    return diffLast1000Blocks


def blockTimeLast200Blocks():
    durationLast200Blocks = []
    lastBlock = last_idInMongo()
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V3"]
    mycol = mydb["mainChain_V3"]
    flag = False
    for i in range((lastBlock-201), lastBlock+1, 1):
        myquery = {'_id': i}
        target = mycol.find_one(myquery)
        blockNumber = target['_id']
        time = target['blockTime']
        if flag is False:
            pastBlockTime = time
            flag = True
            continue
        duration = time - pastBlockTime
        data = {'block_number': blockNumber, 'block_duration': duration}
        durationLast200Blocks.append(data)
        pastBlockTime = time
    myclient.close()
    return durationLast200Blocks


def last_idInMongo():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    target = mycol.find().sort('_id', -1).limit(1)
    # print(target[0])
    lastBlock = target[0]['_id']
    print(lastBlock)
    myclient.close()
    return lastBlock


def replaceInputFieldWithRealAddresses():
    try:
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["SinMain"]
        mycol = mydb["analyzed"]
        target = mycol.find().sort('block', -1).limit(1)
        print(target[0])
        startBlock = target[0]['block']
        myclient.close()
        print(startBlock)
    except:
        startBlock = 0
        print(startBlock)

    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["SinMain"]
    mycol = mydb["blockNumber"]
    target = mycol.find().sort('_id', -1)
    endBlock = target[0]['_id']
    print(endBlock)
    myclient.close()

    inputArrayOfInput = []
    inputArrayOfTx = []
    outList = []
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["SinMain"]
    mycol = mydb["blockNumber"]
    myquery = {"_id": {"$gt": startBlock}}
    target = mycol.find(myquery)
    endBlock = target[0]['_id']
    print(endBlock)

    for block in target:
        blockNumber = block['_id']
        if blockNumber % 100 == 0:
            print(blockNumber)
        txsInBlock = block['txsInBlock']
        for singleTxInBlock in txsInBlock:
            #            print(singleTxInBlock)
            inputFieldOfTx = singleTxInBlock['inputListOfTx']
            outputFieldOfTx = singleTxInBlock['outputListOfTx']
            for singleOutput in outputFieldOfTx:
                adr = singleOutput['outputAddress']
                amm = singleOutput['outputAmount']
                data = {'to_address': adr, 'the_amount': amm}
                outList.append(data)

            Hash = singleTxInBlock['TXhash']
            for singleInputElement in inputFieldOfTx:
                if singleInputElement == 'coinbase':
                    #                    print(singleInputElement)
                    #                    print()
                    inputArrayOfInput = ['coinbase']
                    continue
                else:
                    HashTxInElement = singleInputElement['inputTxid']
                    output_nInElement = singleInputElement['inputTxidOutput_n']
                    analyzedInputTx = findEllement(
                        HashTxInElement)       # call def
                    inputBlock = analyzedInputTx['session2']['tx included in block']
                    outputField = analyzedInputTx['session2']['tx']['outputListOfTx']
                    for singleOutput in outputField:
                        n = singleOutput['output_n']

                        if output_nInElement == n:
                            address = singleOutput['outputAddress']
                            amount = singleOutput['outputAmount']
                            record = {'from_Block': inputBlock,
                                      'from_address': address, 'send_amount': amount}
                            inputArrayOfInput.append(record)
                            break
            payload = {'tx': Hash, 'input': inputArrayOfInput,
                       'output': outList}
            inputArrayOfTx.append(payload)
            inputArrayOfInput = []
            outList = []
        payload1 = {'block': blockNumber, 'txs': inputArrayOfTx}
        myclient1 = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient1["SinMain"]
        mycol = mydb["analyzed"]
        mydict = payload1
        x = mycol.insert_one(mydict)
        myclient1.close()
        inputArrayOfTx = []


def readAllAddressesBalanse():
    b1Mplus = []
    b5Mto10M = []
    b1Mto5M = []
    b500Kto1M = []
    b100Kto500K = []
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["SinMain"]
    mycol = mydb["addressesBalanse"]
    target = mycol.find().sort('balanse', -1)
    array = []
    cursor = 0
    for row in target:
        cursor += 1
        address = row['address']
        balanse = int(row['balanse'])
        if address == 'SinBurnAddress123456789SuqaXbx3AMC' or balanse < 100000:
            continue
        if balanse > 10000000:
            payload = {'name': address, 'balanse': balanse}
            b1Mplus.append(payload)
        elif balanse >= 5000001 and balanse <= 10000000:
            payload = {'name': address, 'balanse': balanse}
            b5Mto10M.append(payload)
        elif balanse >= 1000001 and balanse <= 5000000:
            payload = {'name': address, 'balanse': balanse}
            b1Mto5M.append(payload)
        elif balanse >= 500001 and balanse <= 1000000:
            payload = {'name': address, 'balanse': balanse}
            b500Kto1M.append(payload)
        elif balanse >= 100001 and balanse <= 500000:
            payload = {'name': address, 'balanse': balanse}
            b100Kto500K.append(payload)
    group1 = {'name': '10M +', 'category': b1Mplus}
    group2 = {'name': '5 to 10 M', 'category': b5Mto10M}
    group3 = {'name': '1 to 5 M', 'category': b1Mto5M}
    group4 = {'name': '500K to 1M', 'category': b500Kto1M}
    group5 = {'name': '100K to 500K', 'category': b100Kto500K}

    array = [group1, group2, group3, group4]

    myclient.close()
    return array


def findNodeBasicElements(nodeAddress):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V3"]
    mycol = mydb["activeNodes_V2"]
#    myquery = {"activeNodesList.address": nodeAddress}
    if nodeAddress == 'sortByExpiration':
        target = mycol.find().sort('activeNodesList.end', 1)
        myclient.close()
        return target[0]['activeNodesList']

    target = mycol.find()
    target = target[0]
    array = target['activeNodesList']
    for row in array:
        if row['address'] == nodeAddress:
            print(row)
            return row
    print('error in findNodeBasicElements')
    return 'cant find node with this address'


def pricePeriod(records):
    payload = []
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V2"]
    mycol = mydb["price_db"]
    target = mycol.find().sort('_id', -1).limit(records)
    data = list(target)
    for i in data:
        unixTime = i['_id']
        sinPriceInSatoshis = i['sinPriceInSatoshis']
        sinPriceInUSD = i['sinPriceInUSD']
        btcPriceInUSD = i['btcPriceInUSD']
        timeStamp = time.asctime(time.gmtime(unixTime))
        tempPayload = {'time': timeStamp, 'sinPriceInSatoshis': sinPriceInSatoshis,
                       'sinPriceInUSD': sinPriceInUSD, 'btcPriceInUSD': btcPriceInUSD}
        payload.append(tempPayload)

    return payload


def supply():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]
    target = mycol.find().sort('_id', -1).limit(1)
    supplyFromMain = target[0]['circulatingSupply']

    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["addressesBalance_V4"]
    target = mycol.find().sort('balance', -1)
    supplyFromAddresses = 0
    for row in target:
        supplyFromAddresses += row['balance']
    lastBlockInMongo = last_idInMongo()
    lastBlockInsind = blockHeight()
    deviation = supplyFromAddresses - supplyFromMain

    if lastBlockInMongo != lastBlockInsind:
        #print('Databases in sync with chain.... Block now ', lastBlockInMongo)
        #print('supply from mainchain :', supplyFromMain)
        #print('supply from addresses :', supplyFromAddresses)
        #print('Deviation', deviation)
        payload = {'database in sync with chain blocks calculated': lastBlockInMongo,
                   'circSupplyFromMainDb': supplyFromMain, 'circSupplyFromAddressesDb': supplyFromAddresses, 'supplyDeviation': deviation}
        return payload


# supply()
#ask = pricePeriod(200)
# for i in ask:
#    print(i)
# print(ask)
# ask = findEllement(
#    '74c3c5ce644ea0570aa209c02a944d79a4b3055d779474df88d0e97531f40536')
# print(ask['type'], ask['body']['_id'])
# ask = findEllement(
#    '354eb4b8baa585a2da6bf88a981da4fe834cfe9b441365d20d870813488ddd23')
# print(ask)
#ask = blockTimeLast200Blocks()
# print(ask)
#ask = last_idInMongo()
# print(ask)
#ask = last_idInMongo()
# print(ask)
# difficultyLast200Blocks()
