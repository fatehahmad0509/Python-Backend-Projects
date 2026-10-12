import random
import time


difficulty = int(input("Welcome to the Number Guessing Game! I will think of a number and you will try to guess it. But first, choose a difficulty mode! 1 = Easy, 2 = Medium, 3 = Hard. "))

number = int

if difficulty == 1:
    number = random.randint(1, 10)
    print("I picked a number between 1 and 10!")

elif difficulty == 2:
    number = random.randint(1, 20)
    print("I picked a number between 1 and 20!")

elif difficulty == 3:
    number = random.randint(1, 50)
    print("I picked a number between 1 and 50!")


userguess = int(input("Please Write Your Guess: "))


if userguess == number:
    print("Congratulations! Your answer is correct!")

else:
    print("Unfortunately, you guessed wrong! The number I chose was: " + str(number) )

time.sleep(10)