from data.buildings import BUILDINGS


def buy_property(player, tile):
    if tile.owner is None and player.money >= tile.price:
        player.money -= tile.price
        tile.owner = player
        player.properties.append(tile)
        print(f"{player.name} bought {tile.name}")
        return True
    return False


def upgrade_property(player, tile):
    if tile.owner != player:
        print("You do not own this property.")
        return False

    if tile.level >= 3:
        print("Max level reached.")
        return False

    upgrade_cost = tile.price // 2

    if player.money < upgrade_cost:
        print("Not enough money to upgrade.")
        return False

    player.money -= upgrade_cost
    tile.level += 1

    print(f"{player.name} upgraded {tile.name} to level {tile.level}")
    return True


def can_build(player, tile, building_key):
    if building_key not in BUILDINGS:
        return False, "Unknown building."

    if tile.owner != player:
        return False, "You do not own this property."

    if building_key in tile.buildings:
        return False, "This building already exists on the tile."

    building = BUILDINGS[building_key]

    if player.money < building["cost_money"]:
        return False, "Not enough money."

    for resource_name, required_amount in building["cost_resources"].items():
        if player.resources.get(resource_name, 0) < required_amount:
            return False, f"Not enough {resource_name}."

    return True, "Can build."


def build_on_property(player, tile, building_key):
    can_build_now, message = can_build(player, tile, building_key)
    if not can_build_now:
        print(message)
        return False

    building = BUILDINGS[building_key]

    player.money -= building["cost_money"]
    for resource_name, required_amount in building["cost_resources"].items():
        player.resources[resource_name] -= required_amount

    tile.buildings.append(building_key)
    print(f"{player.name} built {building['name']} on {tile.name}")
    return True


def find_tile_by_name(board, tile_name):
    for tile in board:
        if tile.name == tile_name:
            return tile
    return None