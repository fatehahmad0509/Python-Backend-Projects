import json
import time
import random
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("MAIL_USER")
EMAIL_PASSWORD = os.getenv("MAIL_PASS")


currentbalance = int
try:
    with open("balance.txt", "r") as f:
        currentbalance = int(f.read().strip())
except FileNotFoundError:
    currentbalance = 0
except ValueError:
    currentbalance = 0

repeat = False

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
                time.sleep(1)
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
                time.sleep(1)
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
            whichprocess = int(input("""---Welcome To The NF Bank! Please Select The Process You Want To Do---

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

def loginsuccess():
    mainmenu()

def login():
    global accountinfos
    while True:
        userpassword = input("Welcome To NF Bank! Please enter your password: ")
        if accountinfos["password"] == userpassword:
            print("Login Successful!")
            time.sleep(1)
            loginsuccess()
            break
        else:
            print("Wrong Password. Please try again.")
            time.sleep(1)


def send_welcome_email(to_email, name):
    msg = EmailMessage()
    msg['Subject'] = "Welcome to NF Bank!"
    msg['From'] = "welcome.nfbank@gmail.com"
    msg['To'] = to_email
    msg.set_content(f"Hi {name}, Your NF Bank account has been successfully created! Welcome!")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def openaccount():
    input("""---Welcome To The NF Bank! You Should Open A Bank Account To Use The NF Bank!---
    
-Yes, I Want To Open An Account! (Press Enter) 
""")
    fullname = input("Please enter your full name: ")
    age = int(input("Please enter your age: "))
    birthdate = input("Please enter your birth date: ")
    email = input("Please enter your email address: ")
    password = input("Please enter your password: ")

    userprofile = {
        "fullname": fullname,
        "age": age,
        "birthdate": birthdate,
        "email": email,
        "password": password
    }

    if age < 18:
        print("Sorry, you should be over 18 to open an account.")
        time.sleep(5)
        exit()
    else:
        pass
    print("Registration successful!")
    with open("accountinfos.json", "w") as f:
        json.dump(userprofile, f)
    send_welcome_email(email, fullname)
    return userprofile


try:
    with open("accountinfos.json", "r") as f:
        accountinfos = json.load(f)
except FileNotFoundError:
    currentbalance = 0
    accountinfos = openaccount()

login()

try:
    with open("balance.txt", "r") as f:
        currentbalance = int(f.read().strip())
except FileNotFoundError:
    currentbalance = 0

repeat = True



