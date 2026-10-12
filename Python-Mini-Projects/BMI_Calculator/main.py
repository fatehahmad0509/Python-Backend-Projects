import time

weight = int(input("Welcome to the Body Mass Index (BMI) Calculator! Please enter your weight: "))
height = float(input("Please enter your height in meters:"))

BMI =  float(weight / (height ** 2))


situation = ""

if BMI <= 18.5:
    situation = "Underweight"

elif 18.5 < BMI <= 24.9:
    situation = "Normal"

elif 24.9 < BMI <= 29.9:
    situation = "Overweight"

elif BMI >= 30:
    situation = "Obeze"


print("Your Body Mass Index (BMI): " + str(BMI) + ", Your Situation: " + situation)

time.sleep(10)