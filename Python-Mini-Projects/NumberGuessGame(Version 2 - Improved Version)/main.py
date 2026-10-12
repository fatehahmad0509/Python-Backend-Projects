import random
import time

difficultmode = int(input("Welcome To The Number Guess Game! Select Your Difficult Mode, 1: Easy, 2:Normal, 3:Hard "))

if difficultmode == 1:
    number = random.randint(1,10)
    attemptsleft = 4

elif difficultmode == 2:
    number = random.randint(1,20)
    attemptsleft = 3

elif difficultmode == 3:
    number = random.randint(1,50)
    attemptsleft = 2

userguess = int(input("I Picked A Number, You Have " + str(attemptsleft + 1) + " Attempts, Enter Your Guess: "))

while userguess != number and attemptsleft > 0:
    userguess = int(input("Wrong Guess, You Have " + str(attemptsleft) + " Attempts Left! Enter Your Guess: "))
    attemptsleft -= 1
    if attemptsleft == 0:
        print("Sorry, You Don't Have Any Attempts Left!")



if userguess == number:
    print("Congratulations! You Guessed The Number Right!")


time.sleep(10)