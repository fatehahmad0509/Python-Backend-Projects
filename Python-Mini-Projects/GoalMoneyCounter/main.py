import time

print("Welcome to the Money Counter! Calculate the time left to reach your savings goal")

ownedmoney = float(input("Enter The Money You Have (USD): "))
goalmoney = float(input("Enter Your Goal (USD): "))
monthlydeposit = float(input("Enter Your Monthly Deposit (USD): "))

availablemoney = ownedmoney + monthlydeposit


monthcounter = 1

while availablemoney < goalmoney:
    availablemoney += monthcounter
    monthcounter += 1

else:
    print("Here is the result! You will reach your target amount in", monthcounter, "months!")

time.sleep(10)