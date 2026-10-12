def calculate(number1, number2, whichprocess):
    if whichprocess == "A" or whichprocess == "a":
        return number1 + number2
    elif whichprocess == "S" or whichprocess == "s":
        return number1 - number2
    elif whichprocess == "M" or whichprocess == "m":
        return number1 * number2
    elif whichprocess == "D" or whichprocess == "d":
        return number1/ number2


if __name__ == "__main__":
    from gui import Calc
    Calc().run()