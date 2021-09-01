from authproxy import AuthServiceProxy, rpc_connection


def blockHeight():
    #    print('---------------------- blockHeight --------------------------- ')
    height = rpc_connection.getblockcount()
    return height


ask = blockHeight()
# print(ask)
