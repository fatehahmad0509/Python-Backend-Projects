import random
import time

leverage = int(input("Welcome to the Casino! If you guess correctly, you will win your bet multiplied by the leverage! Enter Leverage: "))
bet_amount = int(input("Please Enter the Amount You Want to Bet: "))
current_balance = bet_amount
game_type = int(input('Now Please Choose Your Game Type: Dice Game: 1, Number Guess: 2, Heads or Tails: 3 '))

if game_type == 1:
    while current_balance > 0:
        rolled_dice = random.randint(1, 6)
        dice_guess = int(input(
            "I rolled the dice! Guess a number between 1 and 6! (Current Balance: " + str(current_balance) + ") "))

        if dice_guess == rolled_dice:
            current_balance += 20 * leverage
            pressentertocontinue = input("Congratulations! Your guess is correct! You Won " + str(20 * leverage) + "! Current Balance: " + (str(current_balance) + ", Press Enter To Continue"))

        elif dice_guess != rolled_dice:
            current_balance -= 60 * leverage
            if current_balance < 0:
                current_balance = 0
            pressentertocontinue = input("Unfortunately your guess is wrong! The dice was: " + str(rolled_dice) + ", Current Balance: " + (str(current_balance) + ", Press Enter To Continue"))

if game_type == 2:
    while current_balance > 0:
        secret_number = random.randint(1, 20)
        user_guess = int(input(
            "I picked a number between 1 and 20! Enter your guess! (Current Balance: " + str(current_balance) + ") "))

        if user_guess == secret_number:
            current_balance += 20 * leverage
            pressentertocontinue = input("Congratulations! Your guess is correct! You Won " + str(20 * leverage) + "! Current Balance: " + (str(current_balance) + ", Press Enter To Continue"))

        elif user_guess != secret_number:
            current_balance -= 50 * leverage
            if current_balance < 0:
                current_balance = 0
            pressentertocontinue = input("Unfortunately your guess is wrong! The number was: " + str(secret_number) + ", Current Balance: " + str(current_balance) + ", Press Enter To Continue")

if game_type == 3:
    while current_balance > 0:
        coin_flip = random.randint(1, 2)
        user_guess = int(input(
            "Heads or Tails? Enter your guess! 1: Heads, 2: Tails, (Current Balance: " + str(current_balance) + ") "))

        if user_guess == coin_flip:
            current_balance += 5 * leverage
            pressentertocontinue = input("Congratulations! Your guess is correct! You Won " + str(5 * leverage) + "! Current Balance: " + str(current_balance) + ", Press Enter To Continue")

        elif user_guess != coin_flip:
            current_balance -= 20 * leverage
            if current_balance < 0:
                current_balance = 0
            pressentertocontinue = input("Unfortunately your guess is wrong! Current Balance: " + str(current_balance) + ", Press Enter To Continue")


if current_balance <= 0:
    print("Unfortunately, you have no money left! Game Over!")

time.sleep(10)