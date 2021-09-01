from authproxy import AuthServiceProxy, rpc_connection
import pymongo
import time
from colored import fg, bg, attr

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
resetColor = attr('reset')

searchedTx = 'b95ccf3e64e20ca1777a5e7ac7e1f21607c684492dc139e4a2d803b6a76aae78'
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Sin_V4"]
mycol = mydb["mainChain_V4"]
myquery = {"_id": 12674}
target = mycol.find_one(myquery)
print(target)
txList = target['analyzedTxsInBlock']
print(color1, txList, resetColor)
for tx in txList:
    txHash = tx['_id']
    if txHash == searchedTx:
        outputSeg = tx['outputSegment']
        for singleOut in outputSeg:
            address = singleOut['outputAddress']
            amount = singleOut['outputAmount']
            if address == 'SQTpqbo1EfWMCUtvGSq9Cdmjc8Esa4HSip' and amount == 1941.22553215:
                singleOut['activatedAmount'] = 2000

                mycol.update_one({'_id': 12674}, {
                    '$set': {'analyzedTxsInBlock': txList}})


time.sleep(10)
for row in target:
    block = row['_id']
    if block > 50000:
        time.sleep(10)
    txsInBlock = row['analyzedTxsInBlock']
    for singleTx in txsInBlock:
        txHash = singleTx['_id']
        txCat = singleTx['txCat']
        if txCat == 'checklocktimeverify':
            fee = singleTx['fees']
            if fee < 0:
                fee = fee * -1
            if fee > 0.1:
                print(color3, 'fee > 1 SIN in tx :',
                      txHash, ' block :', block, 'fee :', fee, resetColor)
