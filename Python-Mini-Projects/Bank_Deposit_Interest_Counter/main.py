import time

print("Welcome to the Bank Deposit Interest Calculator!")

deposit_amount = float(input("Enter the amount you will deposit in the bank (USD): "))
annual_interest_rate = float(input("Now, please enter your bank's ANNUAL interest rate (%): "))
withholding_tax_rate = float(input("Now, please enter the withholding tax rate (%): "))

gross_annual_interest = (deposit_amount * annual_interest_rate) / 100
net_annual_interest = gross_annual_interest * (100 - withholding_tax_rate) / 100
monthly_net_interest = net_annual_interest / 12

print("Your net annual interest income: " + str(net_annual_interest))
print("Your net monthly interest income: " + str(monthly_net_interest))

time.sleep(10)