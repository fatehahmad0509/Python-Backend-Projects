import time
import json
import products
import mainmenu

cart = []
totalshopping = 0

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

try:
    with open ("balance.json", "r", encoding="utf-8") as f:
        balance = json.load(f)
except FileNotFoundError:
    balance = 0
    with open ("balance.json", "w", encoding="utf-8") as f:
        balance = json.dump(balance, f, indent=4, ensure_ascii=False)

def savebalance(balance):
    with open("balance.json", "w", encoding="utf-8") as f:
        json.dump(balance, f, indent=4, ensure_ascii=False)

def savestocks():
    with open("stocks.json", "w") as f:
        json.dump({
            "bread": products.bread.stock,
            "milk": products.milk.stock,
            "egg": products.egg.stock,
            "rice": products.rice.stock,
            "pasta": products.pasta.stock,
            "goudacheese": products.goudacheese.stock,
            "stroopwafel": products.stroopwafel.stock,
            "organicmilk": products.organicmilk.stock,
            "proteinbar": products.proteinbar.stock,
            "water": products.water.stock,
            "fruitjuice": products.fruitjuice.stock,
            "coffee": products.coffee.stock,
            "frozenpizza": products.frozenpizza.stock,
            "sandwich": products.sandwich.stock,
            "microwavemeal": products.microwavemeal.stock,
            "detergent": products.detergent.stock,
            "toiletpaper": products.toiletpaper.stock,
            "shampoo": products.shampoo.stock,
            "cocacola": products.cocacola.stock,
        }, f, indent=4)

def startshopping():
    addnewproduct = 1
    global totalshopping
    totalshopping = 0
    while addnewproduct == 1:
        productnumber = int(input("Please enter the product number: "))
        if productnumber == 1:
            selectedproduct = products.bread.buy()
            totalshopping += products.bread.price
            cart.append(selectedproduct)
        elif productnumber == 2:
            selectedproduct = products.milk.buy()
            totalshopping += products.milk.price
            cart.append(selectedproduct)
        elif productnumber == 3:
            selectedproduct = products.egg.buy()
            totalshopping += products.egg.price
            cart.append(selectedproduct)
        elif productnumber == 4:
            selectedproduct = products.rice.buy()
            totalshopping += products.rice.price
            cart.append(selectedproduct)
        elif productnumber == 5:
            selectedproduct = products.pasta.buy()
            totalshopping += products.pasta.price
            cart.append(selectedproduct)
        elif productnumber == 6:
            selectedproduct = products.goudacheese.buy()
            totalshopping += products.goudacheese.price
            cart.append(selectedproduct)
        elif productnumber == 7:
            selectedproduct = products.stroopwafel.buy()
            totalshopping += products.stroopwafel.price
            cart.append(selectedproduct)
        elif productnumber == 8:
            selectedproduct = products.organicmilk.buy()
            totalshopping += products.organicmilk.price
            cart.append(selectedproduct)
        elif productnumber == 9:
            selectedproduct = products.proteinbar.buy()
            totalshopping += products.proteinbar.price
            cart.append(selectedproduct)
        elif productnumber == 10:
            selectedproduct = products.water.buy()
            totalshopping += products.water.price
            cart.append(selectedproduct)
        elif productnumber == 11:
            selectedproduct = products.fruitjuice.buy()
            totalshopping += products.fruitjuice.price
            cart.append(selectedproduct)
        elif productnumber == 12:
            selectedproduct = products.coffee.buy()
            totalshopping += products.coffee.price
            cart.append(selectedproduct)
        elif productnumber == 13:
            selectedproduct = products.frozenpizza.buy()
            totalshopping += products.frozenpizza.price
            cart.append(selectedproduct)
        elif productnumber == 14:
            selectedproduct = products.sandwich.buy()
            totalshopping += products.sandwich.price
            cart.append(selectedproduct)
        elif productnumber == 15:
            selectedproduct = products.microwavemeal.buy()
            totalshopping += products.microwavemeal.price
            cart.append(selectedproduct)
        elif productnumber == 16:
            selectedproduct = products.detergent.buy()
            totalshopping += products.detergent.price
            cart.append(selectedproduct)
        elif productnumber == 17:
            selectedproduct = products.toiletpaper.buy()
            totalshopping += products.toiletpaper.price
            cart.append(selectedproduct)
        elif productnumber == 18:
            selectedproduct = products.shampoo.buy()
            totalshopping += products.shampoo.price
            cart.append(selectedproduct)
        elif productnumber == 19:
            selectedproduct = products.cocacola.buy()
            totalshopping += products.cocacola.price
            cart.append(selectedproduct)

        else:
            print("Please enter a valid product number")
            time.sleep(1.5)
            startshopping()

        if selectedproduct.instock == False:
            print("Sorry, The product is out of stock, please replenish it as soon as possible.")
            input("Press Enter to go to the main menu")
            mainmenu.startmainmenu()
        addedproduct = int(input("Product Name: " + selectedproduct.name + ", Price: " + str(selectedproduct.price) + ", Do You Want To Add A New Product? 1=Yes, 2=No: "))
        if addedproduct == 2:
            print("Total Shopping: " + str(totalshopping) + " EUR")
            didshoppingaccept()
            break

def getreceipt():
    global totalshopping
    global cart
    print(" ")
    print("---Your Receipt---")
    for productlist in cart:
        print(productlist.name + ": " + str(productlist.price) + " EUR")
    print("Total Shopping: " + str(totalshopping) + " EUR")
    print(" ")
    print("Thanks For Your Shopping!")
    print(" ")
def didshoppingaccept():
 global cart
 try:
    shoppingaccepted = int(input("Do You Accept The Cart? 1=Yes, 2=No: "))
    if shoppingaccepted == 1:
        global balance
        global mainmenu
        if balance < totalshopping:
            print("Sorry, Your Balance is insufficient.")
            time.sleep(1)
            mainmenu.startmainmenu()
        savestocks()
        newbalance = balance - totalshopping
        savebalance(newbalance)
        doyouwantreceipt = int(input("Do You Want Receipt? 1=Yes, 2=No: "))
        if doyouwantreceipt == 1:
            getreceipt()
            input("Press Enter to go back to the main menu...")
            mainmenu.startmainmenu()
        elif doyouwantreceipt == 2:
            cart.clear()
            input("Press Enter to go back to the main menu...")
            mainmenu.startmainmenu()

    elif shoppingaccepted == 2:
        cart.clear()
        print("You will be taken to the main menu in 3 seconds.")
        time.sleep(3)
        mainmenu.startmainmenu()
    else:
        cart.clear()
        print("You entered an unvalid number; you will return to the main menu in 4 seconds.")
        time.sleep(4)
        mainmenu.startmainmenu()
 except ValueError:
        cart.clear()
        print("You entered an unvalid number; you will return to the main menu in 4 seconds.")
        time.sleep(4)
        mainmenu.startmainmenu()

startshopping()