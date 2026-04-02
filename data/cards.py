import random

CARDS = [
    {"text": "Infrastructure boom! +150", "effect": "gain", "amount": 150},
    {"text": "Corruption scandal! -150", "effect": "lose", "amount": 150},
    {"text": "Tax audit! -100", "effect": "lose", "amount": 100},
    {"text": "Foreign investment! +200", "effect": "gain", "amount": 200},
    {"text": "Move to Start", "effect": "move_start"},
    {"text": "Skip next turn", "effect": "skip"},
]

def draw_card():
    return random.choice(CARDS)