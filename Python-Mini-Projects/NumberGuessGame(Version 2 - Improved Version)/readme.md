🎯 Number Guess Game v2

A simple Python console guessing game where the player tries to find a randomly generated number within limited attempts based on difficulty level.

🚀 Features
🎲 Random number generation
🎚️ 3 difficulty levels
🔁 Limited attempts system
❌ Win / lose logic
⚡ Simple and fast CLI gameplay
🎮 Difficulty Levels
Mode	Range	Attempts
Easy	1 - 10	5 total
Normal	1 - 20	4 total
Hard	1 - 50	3 total
🧠 How It Works
Game randomly selects a number
Player selects difficulty
Player tries to guess within limited attempts
Game gives feedback until win or lose
📦 Example Gameplay
Welcome To The Number Guess Game! Select Your Difficult Mode, 1: Easy, 2:Normal, 3:Hard
🎯 Guessing phase
I Picked A Number, You Have 4 Attempts, Enter Your Guess: 7
Wrong Guess, You Have 3 Attempts Left! Enter Your Guess: 12
Wrong Guess, You Have 2 Attempts Left! Enter Your Guess: 9
🏆 Win
Congratulations! You Guessed The Number Right!
💀 Lose
Sorry, You Don't Have Any Attempts Left!
🛠️ Installation
1. Clone repo
git clone https://github.com/yourusername/number-guess-game.git
cd number-guess-game
2. Run game
python main.py
📁 Project Structure
number-guess-game/
│
├── main.py
└── README.md
⚙️ Game Logic
random.randint() generates secret number
Difficulty changes:
number range
attempt count
while loop controls guessing flow
Win condition breaks loop early
⚠️ Notes
Input must be integer
Invalid inputs may crash (no validation yet)
Simple learning project for loops & conditionals
🔮 Future Improvements
🧠 Hint system (higher / lower)
⏱️ Timer mode
🏆 Score system
🔄 Replay button
🖥️ GUI version (Tkinter / CustomTkinter)
🌍 Multiplayer mode (turn-based guessing)
👨‍💻 Author

A fun beginner Python game built to practice:

loops 🔁
conditionals ❓
randomness 🎲
