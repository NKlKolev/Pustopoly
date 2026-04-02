import random
from data.cards import draw_card
from data.buildings import BUILDINGS


import random

def roll_dice():
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    return dice1, dice2, dice1 + dice2


def move_player(player, steps, board):
    old_position = player.position
    new_position = (player.position + steps) % len(board)

    if old_position + steps >= len(board):
        player.money += 200
        print(f"{player.name} passed Start and received 200")

    player.position = new_position
    return board[player.position]


def apply_resource_income(player, tile):
    # Base region resource income
    if tile.resource:
        amount = 1 + tile.level
        player.resources[tile.resource] += amount
        print(f"{player.name} gained {amount} {tile.resource} from {tile.name}")

    # Building-based resource income
    for building_key in tile.buildings:
        building = BUILDINGS[building_key]
        resource_output = building.get("resource_output", {})

        for resource_name, amount in resource_output.items():
            player.resources[resource_name] += amount
            print(f"{player.name} gained {amount} {resource_name} from {building['name']}")


def handle_tile(player, tile, game_state):
    game_state.pending_action = None

    if tile.type == "start":
        print(f"{player.name} landed on Start")

    elif tile.type == "region":
        if tile.owner is None:
            print(f"{tile.name} is available for {tile.price}")
            game_state.pending_action = {
                "type": "run_for_governor",
                "tile_name": tile.name,
            }

        elif tile.owner == player:
            print(f"You own {tile.name}. You can upgrade it.")
            apply_resource_income(player, tile)
            game_state.pending_action = {
                "type": "upgrade_property",
                "tile_name": tile.name,
            }

        else:
            rent = tile.get_rent()

            if tile.name == "Vranevo Island":
                rent = random.randint(1, 6) * 50
                print(f"Vranevo Island special rent rolled: {rent}")

            print(f"Pay rent {rent} to {tile.owner.name}")
            player.money -= rent
            tile.owner.money += rent

    elif tile.type == "tax":
        print("Pay tax 100")
        player.money -= 100

    elif tile.type == "event":
        card = draw_card()
        print(card["text"])

        if card["effect"] == "gain":
            player.money += card["amount"]

        elif card["effect"] == "lose":
            player.money -= card["amount"]

        elif card["effect"] == "move_start":
            player.position = 0
            print(f"{player.name} moved to Start")

        elif card["effect"] == "skip":
            player.skip_turns += 1
            print(f"{player.name} will skip their next turn")