import html
import os
import re
import time
import streamlit as st
import streamlit.components.v1 as components
from supabase_game import create_new_game, save_game_state, load_game_state, rebuild_game_from_state
import base64

def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_optional_base64_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def slugify_region_name(region_name):
    slug = region_name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def get_region_video_path(region_name):
    filename = f"{slugify_region_name(region_name)}.mp4"
    return os.path.join("assets", "regions", filename)


def show_region_win_video(player_name, region_name):
    st.session_state.active_event_media = {
        "type": "region_win",
        "player_name": player_name,
        "region_name": region_name,
        "video_path": get_region_video_path(region_name),
    }
EVENT_CARDS = [
    {
        "title": "Foreign Investment",
        "description": "A foreign investor opens a local office and boosts your budget.",
        "effect_text": "+$200",
        "apply": lambda player, game: setattr(player, "money", player.money + 200),
    },
    {
        "title": "Infrastructure Grant",
        "description": "A state grant helps you upgrade local transport links.",
        "effect_text": "+1 🛣️ infrastructure",
        "apply": lambda player, game: player.resources.__setitem__("infrastructure", player.resources["infrastructure"] + 1),
    },
    {
        "title": "Energy Subsidy",
        "description": "The region receives emergency support for energy supply.",
        "effect_text": "+2 ⚡ energy",
        "apply": lambda player, game: player.resources.__setitem__("energy", player.resources["energy"] + 2),
    },
    {
        "title": "Materials Boom",
        "description": "Construction demand surges and local suppliers benefit.",
        "effect_text": "+2 🧱 materials",
        "apply": lambda player, game: player.resources.__setitem__("materials", player.resources["materials"] + 2),
    },
    {
        "title": "Volunteer Wave",
        "description": "A wave of civic enthusiasm boosts your local workforce.",
        "effect_text": "+2 👷 labor",
        "apply": lambda player, game: player.resources.__setitem__("labor", player.resources["labor"] + 2),
    },
    {
        "title": "Trade Fair",
        "description": "A regional trade fair boosts business activity.",
        "effect_text": "+2 🛒 commerce",
        "apply": lambda player, game: player.resources.__setitem__("commerce", player.resources["commerce"] + 2),
    },
    {
        "title": "Tax Audit",
        "description": "Unexpected auditors arrive and drain your campaign funds.",
        "effect_text": "-$100",
        "apply": lambda player, game: setattr(player, "money", max(0, player.money - 100)),
    },
    {
        "title": "Corruption Scandal",
        "description": "A scandal hits your network and damages your finances.",
        "effect_text": "-$150",
        "apply": lambda player, game: setattr(player, "money", max(0, player.money - 150)),
    },
    {
        "title": "Public Backlash",
        "description": "Public anger forces you to lose your next turn.",
        "effect_text": "Skip 1 turn",
        "apply": lambda player, game: setattr(player, "skip_turns", player.skip_turns + 1),
    },
]


def trigger_event_card(game, player, tile_name):
    ensure_player_resources(player)
    card = random.choice(EVENT_CARDS)
    card["apply"](player, game)

    st.session_state.active_event_card = {
        "player_name": player.name,
        "tile_name": tile_name,
        "title": card["title"],
        "description": card["description"],
        "effect_text": card["effect_text"],
    }

    add_log(f"Event: {player.name} drew '{card['title']}' in {tile_name} ({card['effect_text']}).")
    persist_game(game)


def render_event_card_html():
    event_card = st.session_state.get("active_event_card")
    if not event_card:
        return ""

    title = html.escape(event_card.get("title", "Event"))
    description = html.escape(event_card.get("description", ""))
    effect_text = html.escape(event_card.get("effect_text", ""))
    player_name = html.escape(event_card.get("player_name", "Player"))
    tile_name = html.escape(event_card.get("tile_name", "Event Tile"))

    return f"""
    <style>
    .pusto-event-card-wrap {{
        width: 100%;
        max-width: 760px;
        margin: 0 auto 12px auto;
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(239,246,255,0.96));
        border: 2px solid rgba(31,41,55,0.14);
        border-radius: 20px;
        box-shadow: 0 12px 36px rgba(0,0,0,0.12);
        padding: 16px 18px 16px 18px;
        box-sizing: border-box;
    }}
    .pusto-event-card-kicker {{
        text-align: center;
        font-size: 12px;
        font-weight: 700;
        color: #2563eb;
        letter-spacing: 0.4px;
        margin-bottom: 6px;
        text-transform: uppercase;
    }}
    .pusto-event-card-title {{
        text-align: center;
        font-size: 24px;
        font-weight: 900;
        color: #111827;
        margin-bottom: 10px;
    }}
    .pusto-event-card-description {{
        text-align: center;
        font-size: 15px;
        line-height: 1.45;
        color: #374151;
        margin-bottom: 12px;
    }}
    .pusto-event-card-effect {{
        width: fit-content;
        margin: 0 auto;
        font-size: 16px;
        font-weight: 800;
        color: #111827;
        background: rgba(219,234,254,0.9);
        border: 1px solid rgba(37,99,235,0.18);
        border-radius: 999px;
        padding: 8px 14px;
    }}
    </style>
    <div class="pusto-event-card-wrap">
        <div class="pusto-event-card-kicker">Event Card · {player_name} · {tile_name}</div>
        <div class="pusto-event-card-title">{title}</div>
        <div class="pusto-event-card-description">{description}</div>
        <div class="pusto-event-card-effect">{effect_text}</div>
    </div>
    """

def render_event_video_overlay_html():
    event_media = st.session_state.get("active_event_media")
    if not event_media:
        return ""

    if event_media.get("type") != "region_win":
        return ""

    player_name = html.escape(event_media.get("player_name", "Player"))
    region_name = html.escape(event_media.get("region_name", "region"))
    video_path = event_media.get("video_path")
    video_b64 = get_optional_base64_file(video_path) if video_path else None

    if not video_b64:
        return ""

    caption = f"{player_name} won the election in {region_name}"

    return f"""
    <style>
    .pusto-event-inline-wrap {{
        width: 100%;
        max-width: 760px;
        margin: 0 auto 12px auto;
        background: rgba(255,255,255,0.96);
        border: 2px solid rgba(31,41,55,0.14);
        border-radius: 20px;
        box-shadow: 0 12px 36px rgba(0,0,0,0.16);
        padding: 16px 16px 14px 16px;
        box-sizing: border-box;
    }}
    .pusto-event-title {{
        text-align: center;
        font-size: 22px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 12px;
    }}
    .pusto-event-video {{
        width: 100%;
        max-height: 320px;
        object-fit: cover;
        border-radius: 14px;
        background: #000;
        display: block;
    }}
    </style>
    <div class="pusto-event-inline-wrap">
        <div class="pusto-event-title">{caption}</div>
        <video class="pusto-event-video" autoplay muted playsinline>
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
    </div>
    """

from models.player import Player
from models.game_state import GameState
from data.board import create_board
from data.buildings import BUILDINGS
from core.game_engine import roll_dice, move_player, handle_tile
from core.actions import buy_property, upgrade_property, build_on_property, find_tile_by_name

BUILDING_MAP = {

    "Apartment Complex": "apartment",
    "Factory": "factory",
    "Power Plant": "power_plant",
    "Mall": "mall",
    "Construction Hub": "construction_hub",
}

RESOURCE_EMOJIS = {
    "materials": "🧱",
    "energy": "⚡",
    "labor": "👷",
    "commerce": "🛒",
    "infrastructure": "🛣️",
}


def render_dice_face_html(value):
    faces = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅",
    }

    css = """
    <style>
    .pusto-dice-wrap {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
    }
    .pusto-dice-row {
        display: flex;
        gap: 10px;
    }
    .pusto-die {
        width: 60px;
        height: 60px;
        border-radius: 14px;
        border: 2px solid #111;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.14);
        animation: pustoDicePop 0.45s ease;
        transform-origin: center;
    }
    .pusto-die:nth-child(2) {
        animation-delay: 0.06s;
    }
    .pusto-dice-total {
        font-size: 14px;
        font-weight: 700;
        color: #111;
        background: rgba(255,255,255,0.9);
        padding: 4px 10px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    @keyframes pustoDicePop {
        0% { transform: scale(0.75) rotate(-10deg); opacity: 0.2; }
        45% { transform: scale(1.08) rotate(6deg); opacity: 1; }
        70% { transform: scale(0.96) rotate(-3deg); }
        100% { transform: scale(1) rotate(0deg); opacity: 1; }
    }
    </style>
    """

    if not value:
        return css + "<div style='text-align:center;font-size:30px;'>🎲</div>"

    dice1, dice2, total = value

    return (
        css
        + "<div class='pusto-dice-wrap'>"
        + "<div class='pusto-dice-row'>"
        + f"<div class='pusto-die'>{faces[dice1]}</div>"
        + f"<div class='pusto-die'>{faces[dice2]}</div>"
        + "</div>"
        + f"<div class='pusto-dice-total'>Total: {total}</div>"
        + "</div>"
    )


def setup_game(player_names=None):
    game = GameState()
    game.board = create_board()

    if not player_names:
        player_names = ["Player 1", "Player 2", "Player 3"]

    player_colors = ["#2563eb", "#16a34a", "#dc2626", "#7c3aed", "#ea580c"]

    for i, name in enumerate(player_names):
        p = Player(name)
        p.color = player_colors[i % len(player_colors)]
        game.players.append(p)

    for player in game.players:
        ensure_player_resources(player)
        player.resources["materials"] = 5
        player.resources["energy"] = 5
        player.resources["labor"] = 5
        player.resources["commerce"] = 3
        player.resources["infrastructure"] = 2

    return game

def get_winner(players):
    return max(players, key=lambda p: p.money)

def ensure_player_resources(player):
    defaults = {
        "materials": 0,
        "energy": 0,
        "labor": 0,
        "commerce": 0,
        "infrastructure": 0,
    }

    if not hasattr(player, "resources") or not isinstance(player.resources, dict):
        player.resources = defaults.copy()
        return

    for key, value in defaults.items():
        player.resources.setdefault(key, value)

def get_player_by_name(players, player_name):
    for player in players:
        if player.name == player_name:
            return player
    return None


def is_bot_player(player):
    return player.name.startswith("Bot")


def bot_should_buy_property(player, tile):
    return player.money >= tile.price + 150


def bot_should_upgrade_property(player, tile):
    upgrade_cost = int(tile.price * 0.5)
    return player.money >= upgrade_cost + 150 and tile.level < 3


def bot_choose_building(player, tile):
    priority = ["factory", "power_plant", "mall", "construction_hub", "apartment"]

    for building_key in priority:
        if building_key in tile.buildings:
            continue

        building = BUILDINGS[building_key]
        if player.money < building["cost_money"]:
            continue

        affordable = True
        for resource_name, amount_needed in building["cost_resources"].items():
            if player.resources.get(resource_name, 0) < amount_needed:
                affordable = False
                break

        if affordable:
            return building_key

    return None


def resolve_bot_pending_action(game, player):
    if not game.pending_action:
        return

    action = game.pending_action
    tile = find_tile_by_name(game.board, action["tile_name"])

    if action["type"] == "buy_property":
        if bot_should_buy_property(player, tile):
            resolve_pending_action(game, player, action_choice="buy")
        else:
            resolve_pending_action(game, player, action_choice="skip")

    elif action["type"] == "upgrade_property":
        if bot_should_upgrade_property(player, tile):
            resolve_pending_action(game, player, action_choice="upgrade")
        else:
            resolve_pending_action(game, player, action_choice="skip")


    elif action["type"] == "build_property":

        chosen_building = bot_choose_building(player, tile)

        if chosen_building:

            resolve_pending_action(

                game,

                player,

                action_choice="build",

                building_choice=chosen_building,

            )

        else:

            resolve_pending_action(game, player, action_choice="skip")


    elif action["type"] == "run_for_governor":

        if player.money >= 120:

            player.money -= 120

            success, chance = run_governor_election(player, tile)

            if success:

                add_log(f"{player.name} won the election in {tile.name}.")

                show_region_win_video(player.name, tile.name)

            else:

                add_log(f"{player.name} lost the election in {tile.name}.")

        else:

            add_log(f"{player.name} could not afford to run in {tile.name}.")

        game.pending_action = None


def maybe_open_bot_build_menu(game, player):
    current_tile_name = st.session_state.get("current_tile_name")
    if not current_tile_name:
        return

    tile = find_tile_by_name(game.board, current_tile_name)
    if tile and tile.type == "region" and tile.owner == player:
        chosen_building = bot_choose_building(player, tile)
        if chosen_building is not None:
            game.pending_action = {
                "type": "build_property",
                "tile_name": tile.name,
            }
            resolve_bot_pending_action(game, player)


def run_single_bot_turn(game, player):
    if player.skip_turns > 0:
        player.skip_turns -= 1
        add_log(f"{player.name} skipped their turn.")
        end_turn(game)
        return

    prod_roll, production_messages = production_roll(game)
    add_log(f"Production roll: {prod_roll}")
    for message in production_messages:
        add_log(message)

    dice1, dice2, total = roll_dice()
    st.session_state.last_roll = (dice1, dice2, total)
    tile = move_player(player, total, game.board)
    st.session_state.current_tile_name = tile.name
    add_log(f"{player.name} rolled {dice1} + {dice2} = {total} and landed on {tile.name}.")

    before_snapshot = snapshot_players_state(game.players)
    handle_tile(player, tile, game)
    after_snapshot = snapshot_players_state(game.players)
    log_tile_resolution_changes(game, player, tile, before_snapshot, after_snapshot)

    if tile.type == "event":
        trigger_event_card(game, player, tile.name)

    persist_game(game)

    resolve_bot_pending_action(game, player)
    maybe_open_bot_build_menu(game, player)
    end_turn(game)

def run_bot_turns_until_human(game):
    safety_counter = 0
    while (
        game.round <= 100
        and is_bot_player(game.get_current_player())
        and safety_counter < 20
        and not st.session_state.active_event_media
        and not st.session_state.active_event_card
    ):
        bot_player = game.get_current_player()
        run_single_bot_turn(game, bot_player)
        safety_counter += 1

        if st.session_state.active_event_media or st.session_state.active_event_card:
            break



def can_execute_trade(game, trade_offer):
    proposer = get_player_by_name(game.players, trade_offer["from_player"])
    target = get_player_by_name(game.players, trade_offer["to_player"])

    if proposer is None or target is None:
        return False, "Invalid players in trade."

    offer = trade_offer["offer"]
    request = trade_offer["request"]

    if proposer.money < offer["money"]:
        return False, f"{proposer.name} does not have enough money."
    if target.money < request["money"]:
        return False, f"{target.name} does not have enough money."

    for resource_name in ("materials", "energy", "labor", "commerce", "infrastructure"):
        if proposer.resources[resource_name] < offer[resource_name]:
            return False, f"{proposer.name} does not have enough {resource_name}."
        if target.resources[resource_name] < request[resource_name]:
            return False, f"{target.name} does not have enough {resource_name}."

    return True, "Trade can be executed."


def execute_trade(game, trade_offer):
    proposer = get_player_by_name(game.players, trade_offer["from_player"])
    target = get_player_by_name(game.players, trade_offer["to_player"])

    ok, message = can_execute_trade(game, trade_offer)
    if not ok:
        return False, message

    offer = trade_offer["offer"]
    request = trade_offer["request"]

    proposer.money -= offer["money"]
    target.money += offer["money"]
    target.money -= request["money"]
    proposer.money += request["money"]

    for resource_name in ("materials", "energy", "labor", "commerce", "infrastructure"):
        proposer.resources[resource_name] -= offer[resource_name]
        target.resources[resource_name] += offer[resource_name]

        target.resources[resource_name] -= request[resource_name]
        proposer.resources[resource_name] += request[resource_name]

    return True, "Trade executed successfully."

def ensure_game_highways(game):
    if not hasattr(game, "highways") or not isinstance(game.highways, list):
        game.highways = []
        return

    normalized = []
    for entry in game.highways:
        if isinstance(entry, tuple) and len(entry) == 2:
            normalized.append({
                "regions": tuple(sorted(entry)),
                "owner": None,
            })
        elif isinstance(entry, dict) and "regions" in entry:
            normalized.append({
                "regions": tuple(sorted(entry["regions"])),
                "owner": entry.get("owner"),
            })
    game.highways = normalized


def normalize_highway_pair(region_a, region_b):
    return tuple(sorted([region_a, region_b]))

import random

def run_governor_election(player, tile):
    base_chance = 0.55

    # simple modifiers (we expand later)
    if player.resources["commerce"] >= 3:
        base_chance += 0.05

    if player.resources["labor"] >= 3:
        base_chance += 0.05

    # clamp probability
    win_chance = max(0.2, min(0.9, base_chance))

    roll = random.random()

    if roll <= win_chance:
        tile.owner = player
        player.properties.append(tile)
        return True, win_chance
    else:
        return False, win_chance

def can_run_campaign(player, cost_money=120):
    return player.money >= cost_money


def highway_exists(game, region_a, region_b):
    ensure_game_highways(game)
    pair = normalize_highway_pair(region_a, region_b)
    return any(highway["regions"] == pair for highway in game.highways)


def get_highway_bonus(game, tile_name):
    ensure_game_highways(game)
    bonus = 0
    for highway in game.highways:
        region_a, region_b = highway["regions"]
        if tile_name == region_a or tile_name == region_b:
            bonus += 1
    return bonus

def get_owned_region_names(player):
    return [tile.name for tile in player.properties if tile.type == "region"]


def can_build_highway(game, player, region_a, region_b):
    ensure_game_highways(game)

    if region_a == region_b:
        return False, "Choose two different regions."

    tile_a = find_tile_by_name(game.board, region_a)
    tile_b = find_tile_by_name(game.board, region_b)

    if tile_a is None or tile_b is None:
        return False, "One or both regions do not exist."

    if tile_a.owner != player or tile_b.owner != player:
        return False, "You must own both regions to build a solo highway."

    if highway_exists(game, region_a, region_b):
        return False, "A highway already exists between these regions."

    if player.money < 150:
        return False, "Not enough money."

    if player.resources["materials"] < 2:
        return False, "Not enough materials."

    if player.resources["infrastructure"] < 1:
        return False, "Not enough infrastructure."

    return True, "Can build highway."


def build_highway(game, player, region_a, region_b):
    ok, message = can_build_highway(game, player, region_a, region_b)
    if not ok:
        return False, message

    player.money -= 150
    player.resources["materials"] -= 2
    player.resources["infrastructure"] -= 1

    pair = normalize_highway_pair(region_a, region_b)
    game.highways.append({
        "regions": pair,
        "owner": player.name,
    })

    highway_number = len(game.highways)
    return True, f"Highway H{highway_number} built between {pair[0]} and {pair[1]}."

def ensure_game_railways(game):
    if not hasattr(game, "railways") or not isinstance(game.railways, list):
        game.railways = []
        return

    normalized = []
    for entry in game.railways:
        if isinstance(entry, dict) and "regions" in entry:
            normalized.append({
                "id": entry.get("id"),
                "regions": tuple(sorted(entry["regions"])),
                "owner": entry.get("owner"),
            })
    game.railways = normalized


def normalize_railway_pair(region_a, region_b):
    return tuple(sorted([region_a, region_b]))


def railway_exists(game, region_a, region_b):
    ensure_game_railways(game)
    pair = normalize_railway_pair(region_a, region_b)
    return any(railway["regions"] == pair for railway in game.railways)


def get_tile_railways(game, tile_name):
    ensure_game_railways(game)
    return [railway for railway in game.railways if tile_name in railway["regions"]]

def get_railway_bonus(game, tile_name):
    return len(get_tile_railways(game, tile_name))

def can_build_railway(game, player, region_a, region_b):
    if region_a == region_b:
        return False, "Choose two different regions."

    tile_a = find_tile_by_name(game.board, region_a)
    tile_b = find_tile_by_name(game.board, region_b)

    if tile_a is None or tile_b is None:
        return False, "One or both regions do not exist."

    if tile_a.owner != player or tile_b.owner != player:
        return False, "You must govern both regions to build a railway."

    if railway_exists(game, region_a, region_b):
        return False, "A railway already exists between these regions."

    if player.money < 150:
        return False, "Not enough money."

    if player.resources["materials"] < 2:
        return False, "Not enough materials."

    if player.resources["infrastructure"] < 1:
        return False, "Not enough infrastructure."

    return True, "Can build railway."


def build_railway(game, player, region_a, region_b):
    ensure_game_railways(game)
    ok, message = can_build_railway(game, player, region_a, region_b)
    if not ok:
        return False, message

    player.money -= 150
    player.resources["materials"] -= 2
    player.resources["infrastructure"] -= 1

    pair = normalize_railway_pair(region_a, region_b)
    railway_id = len(game.railways) + 1
    game.railways.append({
        "id": railway_id,
        "regions": pair,
        "owner": player.name,
    })

    persist_game(game)
    return True, f"Railway R{railway_id} built between {pair[0]} and {pair[1]}."

def get_game():
    if "game" not in st.session_state or st.session_state.game is None:
        return None

    game = st.session_state.game
    ensure_game_railways(game)

    for player in game.players:
        ensure_player_resources(player)

    return game
def persist_game(game):
    if "game_id" in st.session_state and game is not None:
        save_game_state(game, st.session_state.game_id)

def add_log(message: str):
    if "log" not in st.session_state:
        st.session_state.log = []
    st.session_state.log.append(message)

def snapshot_players_state(players):
    snapshot = {}
    for player in players:
        ensure_player_resources(player)
        snapshot[player.name] = {
            "money": player.money,
            "resources": player.resources.copy(),
        }
    return snapshot


def format_resource_delta(resource_name, amount):
    emoji = RESOURCE_EMOJIS.get(resource_name, resource_name)
    sign = "+" if amount >= 0 else ""
    return f"{emoji} {sign}{amount}"


def log_tile_resolution_changes(game, acting_player, tile, before_snapshot, after_snapshot):
    acting_before = before_snapshot[acting_player.name]
    acting_after = after_snapshot[acting_player.name]
    money_delta = acting_after["money"] - acting_before["money"]

    if tile.type == "region" and tile.owner and tile.owner != acting_player and money_delta < 0:
        rent_paid = abs(money_delta)
        add_log(f"{acting_player.name} paid ${rent_paid} rent to {tile.owner.name} in {tile.name}.")
        return

    if tile.type == "tax" and money_delta < 0:
        add_log(f"{acting_player.name} paid ${abs(money_delta)} in taxes.")
        return

    if money_delta > 0:
        add_log(f"{acting_player.name} gained ${money_delta} this turn.")
    elif money_delta < 0:
        add_log(f"{acting_player.name} lost ${abs(money_delta)} this turn.")

def render_player_summary_df(players):
    rows = []
    for player in players:
        ensure_player_resources(player)
        property_names = [prop.name for prop in player.properties]
        rows.append(
            {
                "Player": player.name,
                "Money": player.money,
                "Position": player.position,
                "🧱": player.resources["materials"],
                "⚡": player.resources["energy"],
                "👷": player.resources["labor"],
                "🛒": player.resources["commerce"],
                "🛣️": player.resources["infrastructure"],
                "Properties": ", ".join(property_names) if property_names else "None",
                "Skip Turns": player.skip_turns,
            }
        )
    return rows


def render_players_panel_html(players):
    cards_html = ""

    for player in players:
        ensure_player_resources(player)
        property_count = len(player.properties)
        skip_turns = player.skip_turns
        is_bot = " 🤖" if is_bot_player(player) else ""

        cards_html += (
            f"<div class='pusto-player-card'>"
            f"<div class='pusto-player-name'>{html.escape(player.name)}{is_bot}</div>"
            f"<div class='pusto-player-topline'><span>💵 ${player.money}</span><span>📍 {player.position}</span></div>"
            f"<div class='pusto-player-resources'>"
            f"<span>🧱 {player.resources['materials']}</span>"
            f"<span>⚡ {player.resources['energy']}</span>"
            f"<span>👷 {player.resources['labor']}</span>"
            f"<span>🛒 {player.resources['commerce']}</span>"
            f"<span>🛣️ {player.resources['infrastructure']}</span>"
            f"</div>"
            f"<div class='pusto-player-footer'><span>🏘️ {property_count}</span><span>⏭️ {skip_turns}</span></div>"
            f"</div>"
        )

    return (
        "<style>"
        ".pusto-player-grid {display:grid; grid-template-columns:1fr; gap:10px; margin-top:6px;}"
        ".pusto-player-card {background:linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243,244,246,0.95)); border:2px solid rgba(31,41,55,0.16); border-radius:14px; padding:10px 12px; box-shadow:0 2px 8px rgba(0,0,0,0.08);}"
        ".pusto-player-name {font-size:15px; font-weight:800; color:#111827; margin-bottom:6px;}"
        ".pusto-player-topline, .pusto-player-footer {display:flex; justify-content:space-between; gap:10px; font-size:13px; font-weight:700; color:#1f2937;}"
        ".pusto-player-resources {display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:6px; margin:8px 0; font-size:12px; color:#374151; text-align:center;}"
        ".pusto-player-resources span {background:rgba(255,255,255,0.85); border:1px solid rgba(209,213,219,0.9); border-radius:8px; padding:4px 2px; font-weight:700;}"
        "</style>"
        f"<div class='pusto-player-grid'>{cards_html}</div>"
    )


def render_game_rules_html():
    return (
        "<style>"
        ".pusto-rules-card {background:linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243,244,246,0.95)); border:2px solid rgba(31,41,55,0.16); border-radius:14px; padding:12px 14px; box-shadow:0 2px 8px rgba(0,0,0,0.08); color:#111827;}"
        ".pusto-rules-card h4 {margin:10px 0 6px 0; font-size:14px;}"
        ".pusto-rules-card p {margin:0 0 8px 0; font-size:12px; line-height:1.35; color:#374151;}"
        ".pusto-rules-card ul {margin:0 0 8px 18px; padding:0; color:#374151;}"
        ".pusto-rules-card li {font-size:12px; line-height:1.35; margin-bottom:4px;}"
        "</style>"
        "<div class='pusto-rules-card'>"
        "<h4>Core Turn Flow</h4>"
        "<ul>"
        "<li>Each turn starts with a production roll using two dice.</li>"
        "<li>Then the active player rolls two dice to move around the board.</li>"
        "<li>If you land on an ungoverned region, you can run for governor.</li>"
        "<li>If you govern a region, you can later build structures and railways.</li>"
        "</ul>"
        "<h4>Production Numbers</h4>"
        "<p>Numbers do not map globally to resources. Each region has its own production number. When the production dice total matches a region's number, that governed region produces its own resource.</p>"
        "<ul>"
        "<li>🧱 Materials — produced by materials regions.</li>"
        "<li>⚡ Energy — produced by energy regions.</li>"
        "<li>👷 Labor — produced by labor regions.</li>"
        "<li>🛒 Commerce — produced by commerce regions.</li>"
        "<li>🛣️ Infrastructure — mainly gained from construction-related bonuses and some buildings.</li>"
        "</ul>"
        "<h4>Production Formula</h4>"
        "<p>When a region activates, it gives: 1 base output + region level + railway bonus. Buildings can add extra resources on top.</p>"
        "<h4>Governor Elections</h4>"
        "<p>Landing on an ungoverned region lets you run for governor. The campaign currently costs $120. If you win the election, you govern that region and can collect rent from it.</p>"
        "<h4>Buildings</h4>"
        "<p>Buildings cost money and resources. Their effects are shown in the build menu before you confirm construction.</p>"
        "<h4>Railways</h4>"
        "<p>Railways connect two regions you govern. They cost $150, 2 materials, and 1 infrastructure. Each railway touching a region adds +1 production bonus to that region.</p>"
        "<h4>Rent and Taxes</h4>"
        "<p>If you land on another player's governed region, you pay rent. If you land on a tax tile, you pay taxes.</p>"
        "</div>"
    )

def production_roll(game):
    dice1, dice2, total = roll_dice()
    production_messages = []

    for tile in game.board:
        if tile.type == "region" and tile.owner and tile.production_number == total:
            owner = tile.owner

            base_output = 1 + tile.level + get_railway_bonus(game, tile.name)
            owner.resources[tile.resource] += base_output

            resource_changes = [format_resource_delta(tile.resource, base_output)]

            for b in tile.buildings:
                if b == "factory":
                    owner.resources["materials"] += 2
                    resource_changes.append(format_resource_delta("materials", 2))
                elif b == "power_plant":
                    owner.resources["energy"] += 2
                    resource_changes.append(format_resource_delta("energy", 2))
                elif b == "mall":
                    owner.resources["commerce"] += 2
                    resource_changes.append(format_resource_delta("commerce", 2))
                elif b == "construction_hub":
                    owner.resources["infrastructure"] += 2
                    resource_changes.append(format_resource_delta("infrastructure", 2))

            production_messages.append(
                f"Production: {owner.name} received {' | '.join(resource_changes)} from {tile.name}."
            )

    return total, production_messages


def render_board_df(board, players):
    rows = []
    for index, tile in enumerate(board):
        owner_name = tile.owner.name if tile.owner else "None"
        players_on_tile = [player.name for player in players if player.position == index]
        players_text = ", ".join(players_on_tile) if players_on_tile else "-"

        row = {
            "Index": index,
            "Tile": tile.name,
            "Type": tile.type,
            "Owner": owner_name,
            "Players": players_text,
        }

        if tile.type == "region":
            row.update(
                {
                    "Price": tile.price,
                    "Level": tile.level,
                    "Base Rent": tile.base_rent,
                    "Current Rent": tile.get_rent(),
                    "Resource": RESOURCE_EMOJIS.get(tile.resource, tile.resource),
                    "Railway Bonus": get_railway_bonus(game, tile.name),
                    "Buildings": ", ".join(tile.buildings) if tile.buildings else "None",
                }
            )
        else:
            row.update(
                {
                    "Price": "-",
                    "Level": "-",
                    "Base Rent": "-",
                    "Current Rent": "-",
                    "Resource": "-",
                    "Railway Bonus": "-",
                    "Buildings": "-",
                }
            )

        rows.append(row)
    return rows


def render_board_visual_html(board, players, current_tile_name=None):
    total_tiles = len(board)
    if total_tiles > 28:
        raise ValueError("Board visual currently supports up to 28 tiles.")

    rows = 8
    cols = 8

    perimeter_positions = []
    for col in range(cols):
        perimeter_positions.append((rows - 1, col))
    for row in range(rows - 2, -1, -1):
        perimeter_positions.append((row, cols - 1))
    for col in range(cols - 2, -1, -1):
        perimeter_positions.append((0, col))
    for row in range(1, rows - 1):
        perimeter_positions.append((row, 0))

    owner_colors = {
        "Player 1": "rgba(59, 130, 246, 0.18)",
        "Player 2": "rgba(16, 185, 129, 0.18)",
        "Player 3": "rgba(239, 68, 68, 0.18)",
    }

    token_colors = {
        "Player 1": "#2563eb",   # strong blue
        "Player 2": "#16a34a",   # strong green
        "Player 3": "#dc2626",   # strong red
        "Bot 1": "#7c3aed",      # purple
        "Bot 2": "#ea580c",      # orange
    }

    highway_owner_colors = {
        "Player 1": "#3b82f6",
        "Player 2": "#10b981",
        "Player 3": "#ef4444",
        None: "#f59e0b",
    }

    cell_map = {(r, c): "<div class='pusto-empty'></div>" for r in range(rows) for c in range(cols)}
    tile_position_map = {}

    inner_left = 100 / cols
    inner_right = 100 - (100 / cols)
    inner_top = 100 / rows
    inner_bottom = 100 - (100 / rows)

    def get_tile_anchor(row, col):
        x_center = ((col + 0.5) / cols) * 100
        y_center = ((row + 0.5) / rows) * 100

        if row == 0:
            return x_center, inner_top, "top"
        if row == rows - 1:
            return x_center, inner_bottom, "bottom"
        if col == 0:
            return inner_left, y_center, "left"
        return inner_right, y_center, "right"

    perimeter_length = 2 * ((inner_right - inner_left) + (inner_bottom - inner_top))

    def anchor_to_distance(x, y, side):
        if side == "top":
            return x - inner_left
        if side == "right":
            return (inner_right - inner_left) + (y - inner_top)
        if side == "bottom":
            return (inner_right - inner_left) + (inner_bottom - inner_top) + (inner_right - x)
        return (inner_right - inner_left) * 2 + (inner_bottom - inner_top) + (inner_bottom - y)

    def distance_to_point(distance):
        top_len = inner_right - inner_left
        right_len = inner_bottom - inner_top
        bottom_len = inner_right - inner_left

        if distance <= top_len:
            return inner_left + distance, inner_top
        distance -= top_len

        if distance <= right_len:
            return inner_right, inner_top + distance
        distance -= right_len

        if distance <= bottom_len:
            return inner_right - distance, inner_bottom
        distance -= bottom_len

        return inner_left, inner_bottom - distance

    def build_perimeter_route(start_anchor, end_anchor):
        x1, y1, side1 = start_anchor
        x2, y2, side2 = end_anchor

        d1 = anchor_to_distance(x1, y1, side1)
        d2 = anchor_to_distance(x2, y2, side2)

        cw = (d2 - d1) % perimeter_length
        ccw = (d1 - d2) % perimeter_length

        points = [(x1, y1)]
        corner_distances = [
            0,
            inner_right - inner_left,
            (inner_right - inner_left) + (inner_bottom - inner_top),
            (inner_right - inner_left) * 2 + (inner_bottom - inner_top),
            perimeter_length,
        ]

        if cw <= ccw:
            for corner_distance in corner_distances:
                if 0 < (corner_distance - d1) % perimeter_length < cw:
                    points.append(distance_to_point(corner_distance % perimeter_length))
        else:
            for corner_distance in reversed(corner_distances):
                if 0 < (d1 - corner_distance) % perimeter_length < ccw:
                    points.append(distance_to_point(corner_distance % perimeter_length))

        points.append((x2, y2))
        return points

    def offset_route_points(route_points, lane_offset):
        adjusted = []
        for x, y in route_points:
            new_x = x
            new_y = y

            if abs(x - inner_left) < 0.01:
                new_x = x + lane_offset
            elif abs(x - inner_right) < 0.01:
                new_x = x - lane_offset

            if abs(y - inner_top) < 0.01:
                new_y = y + lane_offset
            elif abs(y - inner_bottom) < 0.01:
                new_y = y - lane_offset

            adjusted.append((new_x, new_y))
        return adjusted

    for index, tile in enumerate(board):
        row, col = perimeter_positions[index]
        tile_position_map[tile.name] = {
            "grid": (row, col),
            "anchor": get_tile_anchor(row, col),
        }

        owner_name = tile.owner.name if tile.owner else "None"
        # --- Owner badge visualization enhancement ---
        owner_badge = ""
        if tile.owner:
            owner_color = next((p.color for p in players if p.name == owner_name), "#6b7280")
            owner_initial = html.escape(owner_name.split()[-1][0])
            owner_badge = f"<div class='pusto-owner-badge' style='background:{owner_color};'>{owner_initial}</div>"
        # -------------------------------------------
        owner_bg = owner_colors.get(owner_name, "rgba(255,255,255,0.04)")
        player_border_colors = {
            "Player 1": "#dc2626",  # red
            "Player 2": "#2563eb",  # blue
            "Player 3": "#eab308",  # yellow
            "Bot 1": "#2563eb",
            "Bot 2": "#eab308",
        }

        players_on_tile = [player.name for player in players if player.position == index]

        if players_on_tile:
            border_color = player_border_colors.get(players_on_tile[0], "#f59e0b")
        else:
            border_color = "#f59e0b" if current_tile_name == tile.name else "rgba(255, 255, 255, 0.95)"
        if tile.type == "region":
            resource_band_map = {
                "materials": ("#92400e", "#f59e0b"),
                "energy": ("#1d4ed8", "#60a5fa"),
                "labor": ("#047857", "#34d399"),
                "commerce": ("#7c3aed", "#c4b5fd"),
                "infrastructure": ("#be185d", "#f9a8d4"),
            }
            band_dark, band_light = resource_band_map.get(tile.resource, ("#374151", "#d1d5db"))
            tile_class = "pusto-region"
        elif tile.type == "event":
            band_dark, band_light = "#0f766e", "#99f6e4"
            tile_class = "pusto-event"
        elif tile.type == "tax":
            band_dark, band_light = "#b91c1c", "#fca5a5"
            tile_class = "pusto-tax"
        elif tile.type == "start":
            band_dark, band_light = "#1d4ed8", "#93c5fd"
            tile_class = "pusto-start"
        else:
            band_dark, band_light = "#374151", "#d1d5db"
            tile_class = "pusto-generic"

        token_emoji_map = {
            "Player 1": "🧍🏻",
            "Bot 1": "🧍🏻‍♂️",
            "Bot 2": "🧍🏻‍♀️",
        }

        token_html = "".join(
            f"<span class='pusto-token'>{token_emoji_map.get(player_name, '🧍')}</span>"
            for player_name in players_on_tile
        )

        building_emoji_map = {
            "apartment": "🏬",
            "factory": "🏭",
            "power_plant": "🔋",
            "mall": "🏪",
            "construction_hub": "🏗️",
        }

        buildings_html = ""
        if getattr(tile, "buildings", None):
            emojis = []
            for b in tile.buildings:
                emojis.append(building_emoji_map.get(b, ""))
            if emojis:
                buildings_html = (
                    "<div class='pusto-buildings'>"
                    + "".join(f"<span class='pusto-building'>{e}</span>" for e in emojis if e)
                    + "</div>"
                )

        tile_railways = get_tile_railways(game, tile.name)
        railway_html = ""

        for railway in tile_railways:
            railway_owner = railway.get("owner")
            railway_color = next((p.color for p in players if p.name == railway_owner), "#6b7280")
            railway_html += (
                f"<div class='pusto-railway-marker'>"
                f"<span class='pusto-railway-dot' style='background:{railway_color};'></span>"
                f"<span class='pusto-railway-id'>{railway['id']}🚋</span>"
                f"</div>"
            )
        resource_text = RESOURCE_EMOJIS.get(tile.resource, "-") if getattr(tile, "resource", None) else "-"
        if tile.type == "region":
            region_meta = (
                f"<div class='pusto-resource'>{html.escape(str(resource_text))}</div>"
                f"<div class='pusto-rent'>Rent: {tile.get_rent()}</div>"
            )
        else:
            region_meta = (
                f"<div class='pusto-resource'>-</div>"
                f"<div class='pusto-rent'>{html.escape(tile.type.title())}</div>"
            )

        cell_map[(row, col)] = f'''
        <div class="pusto-tile {tile_class}" style="border-color:{border_color}; background:{owner_bg};">
            {owner_badge}
            <div class="pusto-band" style="background: linear-gradient(90deg, {band_dark}, {band_light});"></div>
            <div class="pusto-title">{html.escape(tile.name)}</div>
            {region_meta}
            <div class="pusto-tokens">{token_html if token_html else "<span class='pusto-no-token'>-</span>"}</div>
            {buildings_html}
            <div class="pusto-railways">{railway_html}</div>
        </div>
        '''

    highway_lines_html = ""


    board_html = """
    <style>
    .pusto-board-wrap {
        position: relative;
        width: 100%;
        max-width: 1090px;
        margin: 12px auto 0 auto;
    }
    .pusto-highways {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
        overflow: visible;
    }
    .pusto-board {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: repeat(8, minmax(58px, 1fr));
        grid-template-rows: repeat(8, 78px);
        gap: 6px;
    }
    .pusto-tile {
        border: 5px solid rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 4px 5px 5px 5px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 78px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.18);
        position: relative;
        overflow: hidden;
        background: rgba(255,255,255,0.96);
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    
        .pusto-tile:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.22);
    }
    .pusto-band {
        height: 9px;
        border-radius: 8px;
        margin-bottom: 4px;
    }
    .pusto-region {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243,244,246,0.96));
    }
    .pusto-event {
        background: linear-gradient(180deg, rgba(240,253,250,0.98), rgba(204,251,241,0.92));
    }
    .pusto-tax {
        background: linear-gradient(180deg, rgba(254,242,242,0.98), rgba(254,226,226,0.92));
    }
    .pusto-start {
        background: linear-gradient(180deg, rgba(239,246,255,0.98), rgba(219,234,254,0.92));
    }
    .pusto-generic {
        background: linear-gradient(180deg, rgba(249,250,251,0.98), rgba(229,231,235,0.92));
    }
    
    .pusto-empty {
        border: 2px dashed rgba(156,163,175,0.45);
        border-radius: 10px;
        background: rgba(255,255,255,0.18);
        min-height: 78px;
    }
    .pusto-title {
        font-size: 12px;
        font-weight: 800;
        line-height: 1.08;
        color: #111827;
        text-align: center;
        text-shadow: none;
        letter-spacing: 0.1px;
    }
    
    .pusto-resource {
        font-size: 16px;
        line-height: 1.0;
        text-align: center;
        filter: saturate(1.1);
    }
    .pusto-rent {
        font-size: 12px;
        line-height: 1.0;
        color: #374151;
        text-align: center;
        font-weight: 700;
        background: rgba(255,255,255,0.65);
        border-radius: 6px;
        padding: 1px 4px;
        align-self: center;
    }
    .pusto-tokens {
        display: flex;
        gap: 3px;
        flex-wrap: wrap;
        margin-top: 2px;
    }
    .pusto-token {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: auto;
        height: auto;
        background: none !important;
        border: none !important;
        font-size: 22px;
        line-height: 1;
    }
    .pusto-no-token {
        color: #6b7280;
        font-size: 8px;
    }
    .pusto-owner-badge {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 16px;
        height: 16px;
        border-radius: 999px;
        color: white;
        font-size: 9px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.3);
    }
    .pusto-center {
        grid-column: 2 / span 6;
        grid-row: 2 / span 6;
        border-radius: 14px;
        background: linear-gradient(145deg, rgba(59,130,246,0.12), rgba(16,185,129,0.10));
        border: 1px solid rgba(255,255,255,0.10);
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 10px;
        color: #f9fafb;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 0.3px;
    }
    .pusto-center-sub {
        display:block;
        margin-top:5px;
        font-size:9px;
        font-weight:500;
        color:#d1d5db;
        letter-spacing: 0;
    }
    .pusto-center-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        border-radius: 10px;
    }
        .pusto-railways {
        position: absolute;
        right: 4px;
        bottom: 4px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        align-items: flex-end;
    }

    .pusto-railway-marker {
        display: flex;
        align-items: center;
        gap: 3px;
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(31,41,55,0.18);
        border-radius: 8px;
        padding: 1px 4px;
        font-size: 8px;
        font-weight: 700;
        color: #111827;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }

    .pusto-railway-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        display: inline-block;
        box-shadow: 0 0 0 1px rgba(0,0,0,0.18);
    }

    .pusto-railway-id {
        white-space: nowrap;
        line-height: 1;
    }
    .pusto-buildings {
    position: absolute;
    left: 4px;
    bottom: 4px;
    display: flex;
    gap: 2px;
    align-items: center;
    }
    
    .pusto-building {
        font-size: 10px;
        background: rgba(255,255,255,0.88);
        border: 1px solid rgba(31,41,55,0.18);
        border-radius: 6px;
        padding: 1px 3px;
        line-height: 1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    </style>
    <div class="pusto-board-wrap">
      <svg class="pusto-highways" viewBox="0 0 100 100" preserveAspectRatio="none">
    """
    board_html += highway_lines_html
    board_html += "</svg><div class='pusto-board'>"

    for r in range(rows):
        for c in range(cols):
            if 1 <= r <= 6 and 1 <= c <= 6:
                if r == 3 and c == 3:
                    board_html += (
                        "<div class='pusto-center'>"
                        f"<img src='data:image/png;base64,{get_base64_image('assets/board_center.png')}' class='pusto-center-img' />"
                        "</div>"
                    )
                continue
            board_html += cell_map[(r, c)]

    board_html += "</div></div>"
    return board_html


def resolve_pending_action(game, player, action_choice=None, building_choice=None):
    if not game.pending_action:
        return False

    action = game.pending_action
    tile = find_tile_by_name(game.board, action["tile_name"])

    if action["type"] == "buy_property":
        if action_choice == "buy":
            success = buy_property(player, tile)
            if success:
                add_log(f"{player.name} bought {tile.name} for ${tile.price}.")
        elif action_choice == "skip":
            add_log(f"{player.name} declined to buy {tile.name}.")
        else:
            return False

    elif action["type"] == "upgrade_property":
        if action_choice == "upgrade":
            success = upgrade_property(player, tile)
            if success:
                add_log(f"{player.name} upgraded {tile.name} to level {tile.level}.")
        elif action_choice == "skip":
            add_log(f"{player.name} skipped upgrading {tile.name}.")
        else:
            return False

    elif action["type"] == "build_property":
        if action_choice == "build" and building_choice:
            if building_choice in BUILDING_MAP:
                building_key = BUILDING_MAP[building_choice]
                building_label = building_choice
            else:
                building_key = building_choice
                reverse_building_map = {v: k for k, v in BUILDING_MAP.items()}
                building_label = reverse_building_map.get(building_key, building_key)

            success = build_on_property(player, tile, building_key)
            if success:
                add_log(f"{player.name} built {building_label} on {tile.name}.")
        elif action_choice == "skip":
            add_log(f"{player.name} skipped building on {tile.name}.")
        else:
            return False

    game.pending_action = None
    persist_game(game)
    return True


def end_turn(game):
    game.next_turn()
    st.session_state.turn_started = False
    st.session_state.last_roll = None
    st.session_state.current_tile_name = None
    st.session_state.build_prompt_tile = None
    persist_game(game)

def render_intro_screen():
    st.title("Pustopoly")

    if "setup_mode" not in st.session_state:
        st.session_state.setup_mode = "three_custom"

    intro_left, intro_center, intro_right = st.columns([1.1, 1.8, 1.1])

    with intro_center:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;">
                <img src="data:image/png;base64,{get_base64_image('assets/board_center.png')}" 
                     style="max-width:520px;width:100%;border-radius:18px;box-shadow:0 6px 18px rgba(0,0,0,0.18);" />
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("## Join Existing Game")

        join_game_id = st.text_input("Enter Game ID to join")

        if st.button("Join Game", use_container_width=True):
            if join_game_id:
                st.session_state.game_id = join_game_id.strip()
                st.session_state.game_started = True
                st.session_state.game = None
                st.rerun()

        st.markdown("## Start Game")

        setup_mode = st.radio(
            "Choose game setup",
            ["Three custom players", "Me + 2 bots"],
            index=0 if st.session_state.setup_mode == "three_custom" else 1,
        )

        if setup_mode == "Three custom players":
            st.session_state.setup_mode = "three_custom"
            player_1_name = st.text_input("Player 1 name", value="Player 1")
            player_2_name = st.text_input("Player 2 name", value="Player 2")
            player_3_name = st.text_input("Player 3 name", value="Player 3")

            if st.button("Start", use_container_width=True, type="primary"):
                player_names = [
                    player_1_name.strip() or "Player 1",
                    player_2_name.strip() or "Player 2",
                    player_3_name.strip() or "Player 3",
                ]
                st.session_state.game = setup_game(player_names)
                st.session_state.log = []
                st.session_state.turn_started = False
                st.session_state.last_roll = None
                st.session_state.current_tile_name = None
                st.session_state.build_prompt_tile = None
                st.session_state.trade_offer = None
                st.session_state.active_event_card = None
                st.session_state.game_started = True
                st.rerun()
        else:
            st.session_state.setup_mode = "me_plus_bots"
            player_1_name = st.text_input("Your name", value="Player 1")

            if st.button("Start", use_container_width=True, type="primary"):
                player_names = [
                    player_1_name.strip() or "Player 1",
                    "Bot 1",
                    "Bot 2",
                ]
                st.session_state.game = setup_game(player_names)
                st.session_state.log = []
                st.session_state.turn_started = False
                st.session_state.last_roll = None
                st.session_state.current_tile_name = None
                st.session_state.build_prompt_tile = None
                st.session_state.trade_offer = None
                st.session_state.active_event_card = None
                st.session_state.game_started = True
                st.rerun()



st.set_page_config(page_title="Pustopoly", layout="wide")
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%);
    }

    .stApp {
        background: linear-gradient(180deg, #e0f2fe 0%, #f0f9ff 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "game_started" not in st.session_state:
    st.session_state.game_started = False
if "game" not in st.session_state:
    st.session_state.game = None
if "log" not in st.session_state:
    st.session_state.log = []
if "turn_started" not in st.session_state:
    st.session_state.turn_started = False
if "last_roll" not in st.session_state:
    st.session_state.last_roll = None
if "current_tile_name" not in st.session_state:
    st.session_state.current_tile_name = None
if "build_prompt_tile" not in st.session_state:
    st.session_state.build_prompt_tile = None
if "trade_offer" not in st.session_state:
    st.session_state.trade_offer = None
if "active_event_media" not in st.session_state:
    st.session_state.active_event_media = None
if "active_event_card" not in st.session_state:
    st.session_state.active_event_card = None
if "action_image" not in st.session_state:
    st.session_state.action_image = None

game = get_game()

if not st.session_state.game_started or game is None:
    render_intro_screen()
    st.stop()

if "game_id" not in st.session_state:
    st.session_state.game_id = create_new_game(game)
elif st.session_state.game is None:
    # joining existing game → do NOT overwrite it
    pass

loaded_state = load_game_state(st.session_state.game_id)
game = rebuild_game_from_state(loaded_state)
st.session_state.game = game

st.write("Game ID:", st.session_state.game_id)






if not st.session_state.active_event_media and not st.session_state.active_event_card:
    run_bot_turns_until_human(game)
player = game.get_current_player()

board_col, side_col = st.columns([4.6, 1.0], gap="large")

with side_col:
    st.subheader("Game Status")

    if st.button("🔄 Start New Game", use_container_width=True):
        st.session_state.game = None
        st.session_state.log = []
        st.session_state.turn_started = False
        st.session_state.last_roll = None
        st.session_state.current_tile_name = None
        st.session_state.build_prompt_tile = None
        st.session_state.trade_offer = None
        st.session_state.active_event_media = None
        st.session_state.active_event_card = None
        st.session_state.game_started = False
        st.rerun()
    with st.expander("Game Rules", expanded=False):
        st.markdown(render_game_rules_html(), unsafe_allow_html=True)
    st.write(f"**Round:** {game.round}")
    st.write(f"**Current Turn:** {player.name}{' 🤖' if is_bot_player(player) else ''}")
    if st.session_state.current_tile_name:
        st.write(f"**Current Tile:** {st.session_state.current_tile_name}")

    st.markdown(render_dice_face_html(st.session_state.last_roll), unsafe_allow_html=True)
    st.write(f"**Turn:** {game.round}")
    st.caption("Bots play automatically when it is their turn.")
    st.subheader("Existing Railways")
    ensure_game_railways(game)
    if game.railways:
        for railway in game.railways:
            region_a, region_b = railway["regions"]
            owner = railway.get("owner") or "Unknown"
            st.write(f"**R{railway['id']}** · {owner}")
            st.caption(f"{region_a} ↔ {region_b}")
    else:
        st.caption("No railways yet.")

    st.subheader("Players")
    st.markdown(render_players_panel_html(game.players), unsafe_allow_html=True)

    if game.round <= 10 and player.name == game.get_current_player().name:
        with st.expander("Trade", expanded=False):
            trade_offer = st.session_state.trade_offer

            if trade_offer is None:
                other_players = [p.name for p in game.players if p.name != player.name]
                trade_target = st.selectbox(
                    "Trade with",
                    other_players,
                    key=f"trade_target_{player.name}",
                )

                st.caption("Offer")
                offer_col1, offer_col2, offer_col3 = st.columns(3)
                with offer_col1:
                    offer_money = st.number_input("Offer Money", min_value=0, step=10, key=f"offer_money_{player.name}")
                    offer_materials = st.number_input("Offer Materials", min_value=0, step=1, key=f"offer_materials_{player.name}")
                with offer_col2:
                    offer_energy = st.number_input("Offer Energy", min_value=0, step=1, key=f"offer_energy_{player.name}")
                    offer_labor = st.number_input("Offer Labor", min_value=0, step=1, key=f"offer_labor_{player.name}")
                with offer_col3:
                    offer_commerce = st.number_input("Offer Commerce", min_value=0, step=1, key=f"offer_commerce_{player.name}")
                    offer_infrastructure = st.number_input("Offer Infrastructure", min_value=0, step=1, key=f"offer_infrastructure_{player.name}")

                st.caption("Request")
                request_col1, request_col2, request_col3 = st.columns(3)
                with request_col1:
                    request_money = st.number_input("Request Money", min_value=0, step=10, key=f"request_money_{player.name}")
                    request_materials = st.number_input("Request Materials", min_value=0, step=1, key=f"request_materials_{player.name}")
                with request_col2:
                    request_energy = st.number_input("Request Energy", min_value=0, step=1, key=f"request_energy_{player.name}")
                    request_labor = st.number_input("Request Labor", min_value=0, step=1, key=f"request_labor_{player.name}")
                with request_col3:
                    request_commerce = st.number_input("Request Commerce", min_value=0, step=1, key=f"request_commerce_{player.name}")
                    request_infrastructure = st.number_input("Request Infrastructure", min_value=0, step=1, key=f"request_infrastructure_{player.name}")

                if st.button("Propose Trade", use_container_width=True):
                    new_trade_offer = {
                        "from_player": player.name,
                        "to_player": trade_target,
                        "offer": {
                            "money": int(offer_money),
                            "materials": int(offer_materials),
                            "energy": int(offer_energy),
                            "labor": int(offer_labor),
                            "commerce": int(offer_commerce),
                            "infrastructure": int(offer_infrastructure),
                        },
                        "request": {
                            "money": int(request_money),
                            "materials": int(request_materials),
                            "energy": int(request_energy),
                            "labor": int(request_labor),
                            "commerce": int(request_commerce),
                            "infrastructure": int(request_infrastructure),
                        },
                    }
                    ok, message = can_execute_trade(game, new_trade_offer)
                    if ok:
                        st.session_state.trade_offer = new_trade_offer
                        add_log(f"{player.name} proposed a trade to {trade_target}.")
                        st.rerun()
                    else:
                        st.warning(message)
            else:
                st.info(
                    f"Trade offer: {trade_offer['from_player']} -> {trade_offer['to_player']} | "
                    f"Offer ${trade_offer['offer']['money']}, 🧱{trade_offer['offer']['materials']}, "
                    f"⚡{trade_offer['offer']['energy']}, 👷{trade_offer['offer']['labor']}, "
                    f"🛒{trade_offer['offer']['commerce']}, 🛣️{trade_offer['offer']['infrastructure']} | "
                    f"Request ${trade_offer['request']['money']}, 🧱{trade_offer['request']['materials']}, "
                    f"⚡{trade_offer['request']['energy']}, 👷{trade_offer['request']['labor']}, "
                    f"🛒{trade_offer['request']['commerce']}, 🛣️{trade_offer['request']['infrastructure']}"
                )

                if player.name == trade_offer["from_player"]:
                    st.warning("Waiting for response from the other player...")
                elif player.name == trade_offer["to_player"]:
                    accept_col, reject_col = st.columns(2)
                    with accept_col:
                        if st.button("Accept Trade", use_container_width=True):
                            success, message = execute_trade(game, trade_offer)
                            if success:
                                add_log(
                                    f"Trade accepted: {trade_offer['from_player']} and {trade_offer['to_player']} exchanged resources."
                                )
                                st.session_state.trade_offer = None
                                st.rerun()
                            else:
                                st.warning(message)
                    with reject_col:
                        if st.button("Reject Trade", use_container_width=True):
                            add_log(f"Trade rejected by {trade_offer['to_player']}.")
                            st.session_state.trade_offer = None
                            st.rerun()
                else:
                    st.caption("Trade in progress between other players.")

        with st.expander("Railways", expanded=False):
            owned_regions = get_owned_region_names(player)
            ensure_game_railways(game)

            if len(owned_regions) >= 2:
                highway_col1, highway_col2 = st.columns(2)
                with highway_col1:
                    highway_region_a = st.selectbox(
                        "From region",
                        owned_regions,
                        key=f"highway_region_a_{player.name}",
                    )
                with highway_col2:
                    highway_region_b_options = [r for r in owned_regions if r != highway_region_a] or owned_regions
                    highway_region_b = st.selectbox(
                        "To region",
                        highway_region_b_options,
                        key=f"highway_region_b_{player.name}",
                    )
                st.caption("Railway cost: $150, 🧱2, 🛣️1")
                if st.button("Build Railway", use_container_width=True):
                    success, message = build_railway(game, player, highway_region_a, highway_region_b)
                    if success:
                        add_log(f"{player.name} built a railway between {highway_region_a} and {highway_region_b}.")
                        st.rerun()
                    else:
                        st.warning(message)
            else:
                st.caption("Own at least two regions to build a railway.")

with board_col:
    st.subheader("Board")


    if game.round > 50:
        winner = get_winner(game.players)
        st.success(f"Game Over! Winner: {winner.name} with ${winner.money}")
        if st.button("Start New Game", use_container_width=True):
            st.session_state.game = None
            st.session_state.log = []
            st.session_state.turn_started = False
            st.session_state.last_roll = None
            st.session_state.current_tile_name = None
            st.session_state.build_prompt_tile = None
            st.session_state.trade_offer = None
            st.session_state.active_event_media = None
            st.session_state.active_event_card = None
            st.session_state.game_started = False
            st.rerun()
    else:
        if player.skip_turns > 0 and not st.session_state.turn_started:
            if st.button("Skip Turn", use_container_width=True):
                player.skip_turns -= 1
                add_log(f"{player.name} skipped their turn.")
                end_turn(game)
                st.rerun()
        elif not st.session_state.turn_started:
            if st.button("Roll Dice", use_container_width=True, type="primary"):
                prod_roll, production_messages = production_roll(game)
                add_log(f"Production roll: {prod_roll}")
                for message in production_messages:
                    add_log(message)

                dice1, dice2, total = roll_dice()
                st.session_state.last_roll = (dice1, dice2, total)
                tile = move_player(player, total, game.board)
                st.session_state.current_tile_name = tile.name
                add_log(f"{player.name} rolled {dice1} + {dice2} = {total} and landed on {tile.name}.")

                before_snapshot = snapshot_players_state(game.players)
                handle_tile(player, tile, game)
                after_snapshot = snapshot_players_state(game.players)
                log_tile_resolution_changes(game, player, tile, before_snapshot, after_snapshot)

                if tile.type == "event":
                    trigger_event_card(game, player, tile.name)

                st.session_state.turn_started = True
                persist_game(game)
                st.rerun()
        else:
            current_tile = find_tile_by_name(game.board, st.session_state.current_tile_name)
            pending = game.pending_action

            if pending:
                if pending["type"] == "buy_property":
                    st.info(f"Buy {current_tile.name} for ${current_tile.price}?")
                    buy_col, skip_col = st.columns(2)
                    with buy_col:
                        if st.button("Buy Property", use_container_width=True):
                            resolve_pending_action(game, player, action_choice="buy")
                            st.rerun()
                    with skip_col:
                        if st.button("Skip Purchase", use_container_width=True):
                            resolve_pending_action(game, player, action_choice="skip")
                            st.rerun()

                elif pending["type"] == "run_for_governor":
                    st.info(f"Run for governor of {current_tile.name}? (Cost: $120)")
                    run_col, skip_col = st.columns(2)

                    with run_col:
                        if st.button("Run Campaign", use_container_width=True):
                            if can_run_campaign(player):
                                player.money -= 120
                                success, chance = run_governor_election(player, current_tile)

                                if success:
                                    add_log(
                                        f"{player.name} WON the election in {current_tile.name} ({int(chance * 100)}%).")
                                    show_region_win_video(player.name, current_tile.name)
                                else:
                                    add_log(
                                        f"{player.name} LOST the election in {current_tile.name} ({int(chance * 100)}%).")

                                game.pending_action = None
                                persist_game(game)
                                st.rerun()
                            else:
                                st.warning("Not enough money to campaign.")

                    with skip_col:
                        if st.button("Skip Campaign", use_container_width=True):
                            add_log(f"{player.name} did not run in {current_tile.name}.")
                            game.pending_action = None
                            st.rerun()


                elif pending["type"] == "build_property":
                    st.info(f"Build on {current_tile.name}")
                    building_choice = st.selectbox(
                        "Choose building",
                        list(BUILDING_MAP.keys()),
                        key=f"building_select_{player.name}_{current_tile.name}",
                    )

                    selected_building_key = BUILDING_MAP[building_choice]
                    selected_building = BUILDINGS[selected_building_key]
                    cost_resources = selected_building.get("cost_resources", {})
                    resource_output = selected_building.get("resource_output", {})
                    rent_multiplier = selected_building.get("rent_multiplier")

                    st.markdown("**Build Cost**")
                    st.caption(
                        f"Money: ${selected_building['cost_money']} | "
                        f"🧱 {cost_resources.get('materials', 0)} | "
                        f"⚡ {cost_resources.get('energy', 0)} | "
                        f"👷 {cost_resources.get('labor', 0)} | "
                        f"🛒 {cost_resources.get('commerce', 0)} | "
                        f"🛣️ {cost_resources.get('infrastructure', 0)}"
                    )

                    output_parts = []
                    for resource_name, amount in resource_output.items():
                        emoji = RESOURCE_EMOJIS.get(resource_name, resource_name)
                        output_parts.append(f"{emoji} +{amount}")

                    if rent_multiplier is not None:
                        output_parts.append(f"Rent x{rent_multiplier}")

                    if output_parts:
                        st.markdown("**Effects**")
                        st.caption(" | ".join(output_parts))

                    build_col, skip_col = st.columns(2)
                    with build_col:
                        if st.button("Construct Building", use_container_width=True):
                            resolve_pending_action(
                                game,
                                player,
                                action_choice="build",
                                building_choice=building_choice,
                            )
                            st.rerun()
                    with skip_col:
                        if st.button("Skip Building", use_container_width=True):
                            resolve_pending_action(game, player, action_choice="skip")
                            st.rerun()
            else:
                if current_tile and current_tile.type == "region" and current_tile.owner == player:
                    control_col1, control_col2 = st.columns(2)
                    with control_col1:
                        if st.button("Open Build Menu", use_container_width=True):
                            game.pending_action = {
                                "type": "build_property",
                                "tile_name": current_tile.name,
                            }
                            st.rerun()
                    with control_col2:
                        if st.button("End Turn", use_container_width=True):
                            end_turn(game)
                            st.rerun()
                else:
                    if st.button("End Turn", use_container_width=True):
                        end_turn(game)
                        st.rerun()

    _, center_controls_video, _ = st.columns([1.2, 1.6, 1.2])
    with center_controls_video:
        if st.session_state.active_event_media:
            close_col_left, close_col_button, close_col_right = st.columns([1.2, 0.8, 1.2])
            with close_col_button:
                if st.button("✕ Close Video", key="close_event_video_inline", use_container_width=True):
                    st.session_state.active_event_media = None
                    st.rerun()
            st.markdown(render_event_video_overlay_html(), unsafe_allow_html=True)


        elif st.session_state.active_event_card:

            close_col_left, close_col_button, close_col_right = st.columns([1.2, 0.8, 1.2])

            with close_col_button:

                if st.button("✕ Close Event", key="close_event_card_inline", use_container_width=True):
                    st.session_state.active_event_card = None

                    end_turn(game)

                    st.rerun()

            st.markdown(render_event_card_html(), unsafe_allow_html=True)

        else:
            st.markdown(render_dice_face_html(st.session_state.last_roll), unsafe_allow_html=True)

    components.html(
        render_board_visual_html(
            game.board,
            game.players,
            st.session_state.current_tile_name,
        ),
        height=760,
        scrolling=False,
    )

    st.subheader("Game Log")
    for entry in reversed(st.session_state.log[-12:]):
        st.write(f"- {entry}")
