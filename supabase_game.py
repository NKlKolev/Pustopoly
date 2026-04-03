from supabase_client import supabase
from models.game_state import GameState
from models.player import Player
from data.board import create_board


def save_game_state(game, game_id):
    game_dict = game.to_dict()
    supabase.table("game_states").update({
        "state": game_dict
    }).eq("id", game_id).execute()

def create_new_game(game):
    game_dict = game.to_dict()

    response = supabase.table("game_states").insert({
        "name": "test_game",
        "state": game_dict
    }).execute()


    return response.data[0]["id"]
def load_game_state(game_id):
    response = supabase.table("game_states") \
        .select("state") \
        .eq("id", game_id) \
        .single() \
        .execute()

    return response.data["state"]
def rebuild_game_from_state(state):
    game = GameState()
    game.board = create_board()
    game.players = []

    game.round = state.get("round", 1)
    game.current_player_index = state.get("current_player_index", 0)

    for player_data in state.get("players", []):
        player = Player(player_data["name"])
        player.money = player_data.get("money", 1000)
        player.position = player_data.get("position", 0)
        player.resources = player_data.get(
            "resources",
            {
                "materials": 0,
                "energy": 0,
                "labor": 0,
                "commerce": 0,
                "infrastructure": 0,
            },
        )
        player.skip_turns = player_data.get("skip_turns", 0)
        player.color = player_data.get("color")
        player.properties = []
        game.players.append(player)

    player_lookup = {p.name: p for p in game.players}

    for saved_tile in state.get("board", []):
        for tile in game.board:
            if tile.name == saved_tile["name"]:
                tile.buildings = saved_tile.get("buildings", [])
                if saved_tile.get("owner"):
                    owner_name = saved_tile["owner"]
                    owner_player = player_lookup.get(owner_name)
                    if owner_player:
                        tile.owner = owner_player
                        owner_player.properties.append(tile)
                break

    return game
