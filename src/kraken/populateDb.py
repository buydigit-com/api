import krakenex
import requests
j=[]
k = krakenex.API(key="LZPTx+FPBNXSt+5g3xv14pJSyOiUyn1LDAZ6ibuXloDGNxrjdfXqF9al",secret="w4Drz7NCz810dOaHGan4hh9eegdi7DSM2VacsnjyTerFAPUnNG8iAPqw0fcycndu7grjVU9TQ1XUJCJ79OZNdQ==")

interested_coin = ["BNB","XRP","BUSD","SOL","MATIC","DOT","DAI","SHIB","LTC","AVAX","ATOM","LINK","XMR","ZEC","DASH","USDP"]
interested_currency = ["EUR","USD","XBT"]

#GET ALL ASSETS AVAILABLE
data = k.query_public('Assets')["result"]
for coin in data:
    coin_parsed = {}
    altname = data[coin]["altname"]
    decimals = data[coin]["decimals"]
    status = data[coin]["status"]
    deposit_methods = []
    #GET ALL DEPOSIT METHODS AVAILABLE
    if altname not in interested_coin:
        continue
    data2 = k.query_private('DepositMethods',{'asset':altname})["result"]
    for method in data2:
        deposit_methods.append(method)

    if len(deposit_methods) == 0:
        continue

    coin_parsed["altname"] = altname
    coin_parsed["decimals"] = decimals
    coin_parsed["status"] = status
    coin_parsed["deposit_methods"] = deposit_methods

    data3 = k.query_public("AssetPairs")["result"]

    trading_pairs = []
    for currency in interested_currency:
        if currency != "XBT":
            pair = f"{altname}{currency}"
        else:
            pair = f"{altname}XBT"
            
        for d in data3:
            if pair == data3[d]["altname"]:
                trading_pairs.append(pair)

    coin_parsed["trading_pairs"] = trading_pairs
    j.append(coin_parsed)

print(j)

data = requests.post("http://api.buydigit.com:5000/kraken/loadData",json=j)

