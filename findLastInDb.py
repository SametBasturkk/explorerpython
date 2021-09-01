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
