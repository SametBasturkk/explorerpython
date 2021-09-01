from authproxy import AuthServiceProxy, rpc_connection
import pymongo
import time
from colored import fg, bg, attr
import sys

color1 = fg(255) + bg(64)
color2 = fg(200) + bg(3)
color3 = fg(0) + bg(190)
color4 = fg(26) + bg(43)
color5 = fg("red") + bg(8) + attr("bold")
color6 = fg("blue") + bg(8) + attr("bold")
color6 = fg("blue") + bg(0) + attr("bold")
resetColor = attr('reset')


def removeBlocks(block):
    myclient = pymongo.MongoClient("mongodb://localhost:27200/")
    mydb = myclient["Sin_V4"]
    mycol = mydb["mainChain_V4"]

    myquery = {"_id": {'$gt': block}}
    mycol.delete_many(myquery)


# removeBlocks(14280)
