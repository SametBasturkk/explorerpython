from authproxy import AuthServiceProxy, rpc_connection
import pymongo
import time
from colored import fg, bg, attr
from findLastInDb import findLastRecordBlockNumberInMongo
import sys

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
resetColor = attr('reset')


def findPreviusBlockSupply_ActiveUtxos(block):
    myclient = pymongo.MongoClient("mongodb://localhost:27200/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]

    if block <= 1:
        supply = 0
        activeUtxo = 0
    else:
        myquery = {"_id": block - 1}
        target = mycol.find_one(myquery)
        supply = target['supplyInCurrentBlock']
        activeUtxo = target['activeUtxoInCurrentBlock']
        print('supply', supply)
    return {'supplyInCurrentBlock': supply, 'activeUtxoInCurrentBlock': activeUtxo}


def currentSupplyActiveUtxos(previusSupplyActiveUtxos, utxoImpactInThisBlock, blockImpactInSupply):
    previusSupply = previusSupplyActiveUtxos['supplyInCurrentBlock']
    previusActiveUtxo = previusSupplyActiveUtxos['activeUtxoInCurrentBlock']

    supplyInCurrentBlock = round(previusSupply + blockImpactInSupply, 8)
    activeUtxoInCurrentBlock = previusActiveUtxo + utxoImpactInThisBlock

    #print('supplyInCurrentBlock', supplyInCurrentBlock)
    #print('activeUtxoInCurrentBlock', activeUtxoInCurrentBlock)
    # sys.stdout.write("\033[F")  # Cursor up one line
    # sys.stdout.write("\033[F")  # Cursor up one line
    # sys.stdout.write("\033[F")  # Cursor up one line

    return{'supplyInCurrentBlock': supplyInCurrentBlock, 'activeUtxoInCurrentBlock': activeUtxoInCurrentBlock}
