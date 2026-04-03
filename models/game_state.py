class GameState:
    def __init__(self):
        self.players = []
        self.current_turn_index = 0
        self.board = []
        self.round = 1
        self.game_log = []
        self.pending_action = None
        self.current_player_index = 0

    def get_current_player(self):
        if not self.players:
            return None
        return self.players[self.current_player_index]

    def next_turn(self):
        if not self.players:
            return

        self.current_player_index += 1

        if self.current_player_index >= len(self.players):
            self.current_player_index = 0
            self.round += 1

    def to_dict(self):
        return {
            "round": self.round,
            "current_player_index": self.current_player_index,
            "turn_started": getattr(self, "turn_started", False),
            "last_roll": getattr(self, "last_roll", None),
            "current_tile_name": getattr(self, "current_tile_name", None),
            "pending_action": getattr(self, "pending_action", None),

            "players": [
                {
                    "name": p.name,
                    "money": p.money,
                    "position": p.position,
                    "resources": p.resources,
                    "skip_turns": getattr(p, "skip_turns", 0),
                    "color": getattr(p, "color", None),
                    "avatar": getattr(p, "avatar", "🧍"),
                    "border_color": getattr(p, "border_color", "#ffffff"),
                }
                for p in self.players
            ],

            "board": [
                 {
                    "name": t.name,
                    "type": t.type,
                    "price": getattr(t, "price", None),
                    "rent": getattr(t, "rent", None),
                    "owner": t.owner.name if getattr(t, "owner", None) else None,
                    "buildings": getattr(t, "buildings", []),
                }
                for t in self.board
            ],
        }
