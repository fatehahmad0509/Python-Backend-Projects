import time
import random

try:
    with open("balance.txt", "r") as f:
        currentbalance = int(f.read().strip())
except FileNotFoundError:
    currentbalance = 0

repeat = True

def wannarepeat():
    time.sleep(1)
    global repeat
    wannarepeat = int(input("""Do you want to go back to the main menu?:
Yes: 1
No: 2
 """))
    if wannarepeat == 1:
        repeat = True
    else:
        finish()

def finish():
    while True:
        try:
            wannarate = int(input("""Would you like to rate our service?
Yes: 1
No: 2
 """))
            if wannarate == 1:
                ratescore = int(input("Please enter the rate score you would like to give to service (1-5): "))
                print("Thank You! We will strive to improve our service as much as possible for valued customers like you.")
            else:
                print("Thank you for using our service! We hope you were satisfied with our service.")
            input("Press Enter to exit...")
            exit()
        except ValueError:
            print("Please enter a valid number.")

def deposit():
    global currentbalance
    global repeat
    while True:
        try:
            moneydeposited = int(input("Please enter the amount you want to deposit: "))
            if moneydeposited <= 0:
                print("Please enter a valid number.")
                continue
            currentbalance = currentbalance + moneydeposited
            print("Deposit successful! Your current balance:", currentbalance)
            print("Amount of money deposited:", moneydeposited)
            savebalance()
            break
        except ValueError:
            print("Please enter a valid number.")
            time.sleep(1)
    wannarepeat()

def withdrawal():
    global currentbalance
    while True:
        try:
            moneytobewithdrawn = int(input("Please enter the amount you want to withdraw: "))
            if moneytobewithdrawn <= 0:
                print("Please enter a valid number.")
                continue
            if currentbalance < moneytobewithdrawn:
                print("Unfortunately, your funds are insufficient.")
                continue
            else:
                currentbalance = currentbalance - moneytobewithdrawn
                print("Transaction successful! Your current balance:", currentbalance)
                print("Amount of money withdrawn:", moneytobewithdrawn)
            savebalance()
            break
        except ValueError:
            print("Please enter a valid number.")
            time.sleep(1)
    wannarepeat()

def balanceinquiry():
    global currentbalance
    print("Your current balance:", currentbalance)
    wannarepeat()

def sendmoney():
    global currentbalance
    while True:
        try:
            input("Please enter the IBAN number to which you wish to send money: ")
            moneytosend = int(input("Please enter the amount you want to send: "))
            if moneytosend <= 0:
                print("Please enter a valid number.")
                continue
            if currentbalance < moneytosend:
                print("Unfortunately, your funds are insufficient.")
                continue
            else:
                currentbalance = currentbalance - moneytosend
                print("Transaction successful! Your current balance:", currentbalance)
            savebalance()
            break
        except ValueError:
            print("Please enter a valid number.")
            time.sleep(1)
    wannarepeat()

def requestmoney():
    global currentbalance
    while True:
        try:
            amounttorequest = int(input("Please enter the amount you want to request: "))
            if amounttorequest <= 0:
                print("Please enter a valid number.")
                continue
            persontorequest = input("Please enter the IBAN number to request payment: ")
            print("Your request has been received, please wait...")
            time.sleep(2.5)
            acceptornot = random.randint(1,3)
            if acceptornot == 1:
                print("Unfortunately, The other party did not approve your request for payment.")
            elif acceptornot == 2:
                print("Unfortunately, The other party did not respond your request for payment.")
            else:
                currentbalance = currentbalance + amounttorequest
                print("The other party has approved your request, and the payment has been processed to you!")
                print("Your current balance:", currentbalance)
                print("Amount of money requested:", amounttorequest)
            savebalance()
            break
        except ValueError:
            print("Please enter a valid number.")
    wannarepeat()

def savebalance():
    with open("balance.txt", "w") as f:
        f.write(str(currentbalance))

def mainmenu():
    while True:
        try:
            whichprocess = int(input("""---Welcome To The ATM! Please Select The Process You Want To Do Below---

-Deposit: 1
-Withdrawal: 2
-Balance Inquiry: 3
-Send Money: 4
-Request Money: 5 
"""))
            if whichprocess == 1:
                deposit()
            elif whichprocess == 2:
                withdrawal()
            elif whichprocess == 3:
                balanceinquiry()
            elif whichprocess == 4:
                sendmoney()
            elif whichprocess == 5:
                requestmoney()
        except ValueError:
            print("Please enter a valid number.")

while repeat:
    mainmenu()