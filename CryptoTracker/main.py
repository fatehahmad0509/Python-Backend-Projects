import requests

def getprices():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,tether,binancecoin,solana,ripple,usd-coin,cardano,dogecoin,tron&vs_currencies=usd"
    prices = requests.get(url)
    pricedata = prices.json()
    return {
        "BTC": pricedata["bitcoin"]["usd"],
        "ETH": pricedata["ethereum"]["usd"],
        "USDT": pricedata["tether"]["usd"],
        "BNB": pricedata["binancecoin"]["usd"],
        "SOL": pricedata["solana"]["usd"],
        "XRP": pricedata["ripple"]["usd"],
        "USDC": pricedata["usd-coin"]["usd"],
        "ADA": pricedata["cardano"]["usd"],
        "DOGE": pricedata["dogecoin"]["usd"],
        "TRX": pricedata["tron"]["usd"],
    }

data = getprices()
