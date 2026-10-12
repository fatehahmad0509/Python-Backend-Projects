import time
import requests

url = "https://v6.exchangerate-api.com/v6/37a7c759381d6de8cc36abb7/latest/USD"
response = requests.get(url)
data = response.json()

print("""Welcome To Exchange List! Here Are Some Exchanges!;
 """)

usdtotry = data["conversion_rates"]["TRY"]
print("1 USD =", usdtotry, "TRY")
usdtoeur = data["conversion_rates"]["EUR"]
eurtotry = usdtotry / usdtoeur
print("1 EUR =", eurtotry, "TRY")
usdtoazn = data["conversion_rates"]["AZN"]
azntotry = usdtotry / usdtoazn
print("1 AZN =", azntotry, "TRY")
usdtogbp = data["conversion_rates"]["GBP"]
gbptotry = usdtotry / usdtogbp
print("1 GBP =", gbptotry, "TRY")
usdtojpy = data["conversion_rates"]["JPY"]
jpytotry = usdtotry / usdtojpy
print("1 JPY =", jpytotry, "TRY")
usdtochf = data["conversion_rates"]["CHF"]
chftotry = usdtotry / usdtochf
print("1 CHF =", chftotry, "TRY")
usdtoaud = data["conversion_rates"]["AUD"]
audtotry = usdtotry / usdtoaud
print("1 AUD =", audtotry, "TRY")
usdtocad = data["conversion_rates"]["CAD"]
cadtotry = usdtotry / usdtocad
print("1 CAD =", cadtotry, "TRY")
usdtocny = data["conversion_rates"]["CNY"]
cnytotry = usdtotry / usdtocny
print("1 CNY =", cnytotry, "TRY")
usdtonzd = data["conversion_rates"]["NZD"]
nzdtotry = usdtotry / usdtonzd
print("1 NZD =", nzdtotry, "TRY")

time.sleep(100000)