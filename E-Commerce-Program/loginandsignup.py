import json
import time
import products

def save_data(data):
    with open("accountinfos.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def login(userinfos):
    print("Welcome To The Ecommerce.com!")
    loginpassword = input("Please Enter Your Password: ")
    if loginpassword == userinfos["password"]:
        print("Login Successful!")
        time.sleep(1)
        import mainmenu
        mainmenu
    else:
        print("Wrong password")
        time.sleep(5)
        login(accountinfos)

def signup():
    print("Welcome To The Ecommerce.com! First, You Should Sign Up!")
    name = input("Enter your full name: ")
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    birthdate = input("Enter your birthdate: ")
    age = input("Enter your age: ")
    userinfos = {
       "name": name,
       "email": email,
       "password": password,
       "birthdate": birthdate,
       "age": age}
    save_data(userinfos)
    print("Sign Up Successful!")
    time.sleep(1)
    login(accountinfos)

try:
    with open ("accountinfos.json", "r", encoding="utf-8") as f:
        accountinfos = json.load(f)
        login(accountinfos)
except FileNotFoundError:
    accountinfos = {}
    signup()



try:
    with open("stocks.json", "r") as config:
        data = json.load(fp=config)
    products.bread.stock = data["bread"]
    products.bread.price = data.get("bread_price", products.bread.price)
    products.milk.stock = data["milk"]
    products.milk.price = data.get("milk_price", products.milk.price)
    products.egg.stock = data["egg"]
    products.egg.price = data.get("egg_price", products.egg.price)
    products.rice.stock = data["rice"]
    products.rice.price = data.get("rice_price", products.rice.price)
    products.pasta.stock = data["pasta"]
    products.pasta.price = data.get("pasta_price", products.pasta.price)
    products.goudacheese.stock = data["goudacheese"]
    products.goudacheese.price = data.get("goudacheese_price", products.goudacheese.price)
    products.stroopwafel.stock = data["stroopwafel"]
    products.stroopwafel.price = data.get("stroopwafel_price", products.stroopwafel.price)
    products.organicmilk.stock = data["organicmilk"]
    products.organicmilk.price = data.get("organicmilk_price", products.organicmilk.price)
    products.proteinbar.stock = data["proteinbar"]
    products.proteinbar.price = data.get("proteinbar_price", products.proteinbar.price)
    products.water.stock = data["water"]
    products.water.price = data.get("water_price", products.water.price)
    products.fruitjuice.stock = data["fruitjuice"]
    products.fruitjuice.price = data.get("fruitjuice_price", products.fruitjuice.price)
    products.coffee.stock = data["coffee"]
    products.coffee.price = data.get("coffee_price", products.coffee.price)
    products.frozenpizza.stock = data["frozenpizza"]
    products.frozenpizza.price = data.get("frozenpizza_price", products.frozenpizza.price)
    products.sandwich.stock = data["sandwich"]
    products.sandwich.price = data.get("sandwich_price", products.sandwich.price)
    products.microwavemeal.stock = data["microwavemeal"]
    products.microwavemeal.price = data.get("microwavemeal_price", products.microwavemeal.price)
    products.detergent.stock = data["detergent"]
    products.detergent.price = data.get("detergent_price", products.detergent.price)
    products.toiletpaper.stock = data["toiletpaper"]
    products.toiletpaper.price = data.get("toiletpaper_price", products.toiletpaper.price)
    products.shampoo.stock = data["shampoo"]
    products.shampoo.price = data.get("shampoo_price", products.shampoo.price)
    products.cocacola.stock = data["cocacola"]
    products.cocacola.price = data.get("cocacola_price", products.cocacola.price)
except FileNotFoundError:
    pass