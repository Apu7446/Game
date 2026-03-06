# 🚀 Space Typing Shooter

A fast-paced arcade typing game built with **Pygame** where you destroy alien enemies by typing words!

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green?logo=python&logoColor=white)

## 🎮 Gameplay

- Alien enemies descend from the top of the screen, each carrying a word.
- **Type the word** to fire bullets and destroy the alien before it reaches your ship.
- Survive **1 minute** of waves, then face a **Boss** at the end of each level.
- Progress through **10 levels** with increasing difficulty (Easy → Medium → Hard).
- Build **combos** by typing words correctly in a row for bonus points!

## 🕹️ Controls

| Key       | Action                  |
|-----------|-------------------------|
| `A-Z`     | Type letters to attack  |
| `Backspace` | Delete last character |
| `Enter`   | Clear typed text        |
| `Tab`     | Pause / Resume          |
| `Escape`  | Quit level              |
| `R`       | Restart (on Game Over)  |
| `Q`       | Quit (on Game Over)     |

## ✨ Features

- **10 levels** with progressive difficulty and unique boss fights
- **Real bullet projectiles** — each typed letter fires a homing bullet
- **Combo system** with score multipliers
- **Particle effects** for explosions and hits
- **Auto-aim** ship that rotates toward the current target
- **Boss battles** with HP bars, enemy bullets, and multi-phase attacks
- **Minimalist space aesthetic** with star-scrolling background

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/Apu7446/Game.git
cd Game

# Install dependencies
pip install -r requirements.txt

# Run the game
python space_typing.py
```

## 📁 Project Structure

```
Game/
├── space_typing.py     # Main game source code
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## 🎯 Level Progression

| Level | Difficulty | Enemy Speed | Boss HP |
|-------|-----------|------------|---------|
| 1-3   | Easy      | 0.6 - 0.8 | 3-4     |
| 4-6   | Medium    | 0.9 - 1.1 | 5-6     |
| 7-9   | Hard      | 1.2 - 1.4 | 7-9     |
| 10    | Hard      | 1.6        | 15      |

## 📸 Screenshots

*Coming soon!*

## 🛠️ Built With

- [Python](https://www.python.org/) — Programming language
- [Pygame](https://www.pygame.org/) — Game development library

## 📄 License

This project is open source and available for personal and educational use.
