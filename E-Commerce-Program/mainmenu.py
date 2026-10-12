import json
import time
import mainmenu



def savebalance(balance):
    with open("balance.json", "w", encoding="utf-8") as f:
        json.dump(balance, f, indent=4, ensure_ascii=False)

def startmainmenu():
    try:
        with open("balance.json", "r", encoding="utf-8") as f:
            balance = json.load(f)
    except FileNotFoundError:
        balance = 0
    whichprocess = int(input("""Please enter the process you want: 

1: Shopping
2: Balance Top Up
3: Withdraw Money
4: Sign Out
"""))

    if whichprocess == 1:
        import shopping
        shopping.startshopping()
    elif whichprocess == 2:
        amount = int(input("Please enter the top up amount: "))
        balance = balance + amount
        savebalance(balance)
        print("Your current balance is: ", str(balance), " EUR")
        time.sleep(1)
        mainmenu.startmainmenu()
    elif whichprocess == 3:
        amount = int(input("Please enter the withdraw amount: "))
        if amount > balance:
            print("You cannot enter a value greater than your balance.")
            time.sleep(1)
            mainmenu.startmainmenu()
        balance = balance - amount
        savebalance(balance)
        print("Your current balance is: ", str(balance), " EUR")
        time.sleep(1)
        mainmenu.startmainmenu()
    elif whichprocess == 4:
        import loginandsignup
        loginandsignup.login()

startmainmenu()