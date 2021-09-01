import pymongo

from colored import fg, bg, attr
from checkIfDbExists import checkIfDbExists

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
resetColor = attr('reset')


'''
def findLastBlockWhoUpdateTheAddressesDb():
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["addressesBalance_V4"]
    responce = mycol.find().limit(1).sort([('lastUpdatedInBlock', -1)])
    lastBlockInAddressesDb = responce[0]['lastUpdatedInBlock']
    return lastBlockInAddressesDb
'''


def findLastRecordBlockNumberInMongo():

    localHeight = 0
    dbFlag = checkIfDbExists()
    print(color1, 'flag :', dbFlag, resetColor)
    myclient = pymongo.MongoClient("mongodb://localhost:27200/")
    database = myclient.Sin_V4
    collectionsList = (database.list_collection_names())
    if 'mainChain_V4' in collectionsList:
        print("Exist")
        mydb = myclient["Sin_V4"]
        mycol = mydb["mainChain_V4"]
        mydoc = mycol.find().sort("_id", -1)
        for i in mydoc:
            bestHeightInMongo = i['_id']
            break
        myquery = {"_id": bestHeightInMongo}
        target = mycol.find_one(myquery)
        #print(color1, 'target :', target, resetColor)
        mycol.delete_one(target)
        return bestHeightInMongo
        '''
        if bestHeightInMongo > 0:
            lastInAddressesDb = findLastBlockWhoUpdateTheAddressesDb()
            myquery = {"_id": bestHeightInMongo}
            target = mycol.find_one(myquery)
            addressesToRecalcBalance = target['addressesIvnolvedInBlock']
            arrayToRecalcUtxo = target['analyzedTxsInBlock']
            mycol.delete_one(myquery)
            print(color3, 'Last block in MainChain   :',
                  bestHeightInMongo, resetColor)
            print(color3, 'Last block in AddressesDb :',
                  lastInAddressesDb, resetColor)
            if bestHeightInMongo != lastInAddressesDb:
                print(color1, '___ATENSION___')
                # (10)
            print('Preparation to remove block ', bestHeightInMongo)
            # print('block ', bestHeightInMongo,
            #      ' deleted from database for security reasons and recreated...')
            myclient.close()

            myclient = pymongo.MongoClient("mongodb://localhost:27017/")
            mydb = myclient["Sin_V4"]
            mycol = mydb["addressesBalance_V4"]

            for arrayRow in addressesToRecalcBalance:
                address = arrayRow['address']
                amount = arrayRow['amountInThisBlock']
                myquery = {"_id": address}
                target = mycol.find_one(myquery)
                if target == None:
                    print('New address (', address, ')... created record')
                    record = {'_id': address, 'balance': amount,
                              'lastUpdatedInBlock': block}
                    mycol.insert_one(record)
                else:
                    previusBalance = target['balance']
                    newBalance = previusBalance - amount
                    mycol.update_many({'_id': address}, {'$set':
                                                         {'balance': newBalance, 'lastUpdatedInBlock': 0}})
                    print('Old address ... update record')

            myclient = pymongo.MongoClient("mongodb://localhost:27017/")
            mydb = myclient["Sin_V4"]
            mycol = mydb["utxo_V4"]

            for singleTx in arrayToRecalcUtxo:
                txHash = singleTx['_id']
                txInputSegment = singleTx['inputSegment']
                txOuputSegment = singleTx['outputSegment']

                #     XXX   UTXO  remove     XXX
                for singleTxOut in txOuputSegment:
                    # print('txOuputSegment ', txOuputSegment)
                    # print('singleTxOut ', singleTxOut)
                    address = singleTxOut['outputAddress']
                    sn = str(singleTxOut['output_n'])
                    searchedId = txHash + '_' + sn + '_' + address
                    # searchedId = rowTxInHash + '_' + sn + '_' + rowTxInAddress
                    myquery = {"_id": searchedId}
                    target = mycol.find_one(myquery)
                    if len(list(target)) != 0:
                        id2remove = target['_id']
                        removeElement = {"_id": id2remove}
                        print(color1, 'remove record from utxo Db :',
                              id2remove, resetColor)
                        mycol.delete_one(removeElement)
                    else:
                        print(color3, 'no record ', searchedId,
                              'in utxo Db....', resetColor)
                    myquery = {'blockIncluded': {'$gt': bestHeightInMongo}}
                    mycol.delete_many(myquery)

                    # try:
                    #    addrAmount = singleTxOut['activatedAmount']
                    # except:
                    #    addrAmount = singleTxOut['outputAmount']
                    # payload = {'_id': id, 'blockIncluded': block,
                    #           'txHash': txHash, 'address': address, 'amount': addrAmount}
                    # mycol.insert_one(payload)

                #     XXX   UTXO  add     XXX
                for singleTxIn in txInputSegment:
                    # print('txInputSegment', txInputSegment)
                    # print('singleTxIn', singleTxIn)
                    if singleTxIn != 'coinbase':
                        rowTxInHash = singleTxIn['txHash']
                        rowTxInAddress = singleTxIn['address']
                        sn = str(singleTxIn['outputSN'])
                        id = rowTxInHash + '_' + sn + '_' + rowTxInAddress
                        try:
                            addrAmount = singleTxOut['activatedAmount']
                        except:
                            addrAmount = singleTxOut['outputAmount']
                            payload = {'_id': id, 'blockIncluded': block,
                                       'txHash': txHash, 'address': address, 'amount': addrAmount}
                            print(color2, 'restore record in utxo Db :',
                                  target, resetColor)
                            mycol.insert_one(payload)

                        # searchedId = rowTxInHash + '_' + sn + '_' + rowTxInAddress
                        # myquery = {"_id": searchedId}
                        # target = mycol.find_one(myquery)
                        # print(color1, 'target :', target, resetColor)
                        # mycol.delete_one(target)

            print(color1, "Block ", bestHeightInMongo,
                  " deleted from database for security reasons and recreated...", resetColor)
            # (10)
            return bestHeightInMongo
        else:
            myclient.close()
        '''
    else:
        mydb = myclient["Sin_V4"]
        mycol = mydb["mainChain_V4"]
        mydict = {
            '_id': 0, 'blockHash': "000032bd27c65ec42967b7854a49df222abdfae8d9350a61083af8eab2a25e03", 'circulatingSupply': 0}
        mycol.insert_one(mydict)

        # mydb = myclient["Sin_V4"]
        # mycol = mydb["addressesBalance_V4"]

        # mydb = myclient["Sin_V4"]
        # mycol = mydb["utxo_V4"]
        print('databases not exists... created')
        # (5)
        return 1
