def render_player_summary(players):
    lines = []
    lines.append("=== Players ===")

    for player in players:
        property_names = [prop.name for prop in player.properties]
        properties_text = ", ".join(property_names) if property_names else "None"

        lines.append(
            f"{player.name} | ${player.money} | Pos: {player.position} | "
            f"Res: M{player.resources['materials']} E{player.resources['energy']} L{player.resources['labor']} | "
            f"Props: {properties_text}"
        )

    return "\n".join(lines)


def render_board(board, players):
    lines = []
    lines.append("=== Board ===")

    for index, tile in enumerate(board):
        owner_name = tile.owner.name if tile.owner else "None"

        players_on_tile = [player.name for player in players if player.position == index]
        players_text = ", ".join(players_on_tile) if players_on_tile else "-"

        if tile.type == "region":
            buildings_text = ", ".join(tile.buildings) if tile.buildings else "None"
            tile_text = (
                f"[{index}] {tile.name} | Lvl: {tile.level} | Base Rent: {tile.base_rent} | "
                f"Current Rent: {tile.get_rent()} | Resource: {tile.resource} | "
                f"Buildings: {buildings_text} | Owner: {owner_name} | Players: {players_text}"
            )
        else:
            tile_text = (
                f"[{index}] {tile.name} | Type: {tile.type} | Owner: {owner_name} | Players: {players_text}"
            )

        lines.append(tile_text)

    return "\n".join(lines)