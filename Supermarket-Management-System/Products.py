class product:
    def __init__(self, name, price, code, stock, instock):
        self.name = name
        self.price = price
        self.code = code
        self.stock = stock
        self.instock = instock
    def show_info(self):
        print("Name: " + self.name)
        print("Price: " + self.price)
        print("Stock: " + self.stock)
        print("Instock: " + self.instock)
    def buy(self):
        if self.stock > 0:
            self.stock -= 1
        else:
            self.instock = False
            print("OUT OF STOCK")
        return self

bread = product("Bread", 1, 1, 1000, True)
milk = product("Milk (1L)", 2, 2, 1000, True)
egg = product("Egg (10)", 4, 3, 1000, True)
rice = product("Rice (1KG)", 5, 4, 1000, True)
pasta = product("Pasta", 2.5, 5, 1000, True)
goudacheese = product("Gouda Cheese", 7, 6, 1000, True)
stroopwafel = product("Stroopwafel Cheese", 4, 7, 1000, True)
organicmilk = product("Organic Milk", 3, 8, 1000, True)
proteinbar = product("Protein Bar", 3, 9, 1000, True)
water = product("Water (500ML)", 1, 10, 1000, True)
fruitjuice = product("Fruit Juice", 2.5, 11, 1000, True)
coffee = product("Coffee", 4, 12, 1000, True)
frozenpizza = product("Frozen Pizza", 5, 13, 1000, True)
sandwich = product("Sandwich", 3, 14, 1000, True)
microwavemeal = product("Microwave Meal", 7, 15, 1000, True)
detergent = product("Detergent", 8, 16, 1000, True)
toiletpaper = product("Toilet Paper", 6, 17, 1000, True)
shampoo = product("Shampoo", 7, 18, 1000, True)
cocacola = product("Cocacola", 4, 19, 1000, True)