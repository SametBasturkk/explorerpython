import pymongo


def checkIfDbExists():
    myclient = pymongo.MongoClient("mongodb://localhost:27200/")
    dbnames = myclient.list_database_names()
    if 'Sin_V4' in dbnames:
        print('Sin_V4 exists in mongo ....')
        return 'true'
    else:
        print('Sin_V4 not exists in mongo ....')
        return 'false'
