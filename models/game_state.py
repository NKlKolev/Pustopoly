class GameState:
    def __init__(self):
        self.players = []
        self.current_turn_index = 0
        self.board = []
        self.round = 1
        self.game_log = []
        self.pending_action = None

    def get_current_player(self):
        return self.players[self.current_turn_index]

    def next_turn(self):
        self.current_turn_index = (self.current_turn_index + 1) % len(self.players)
        if self.current_turn_index == 0:
            self.round += 1
        self.pending_action = None

    def to_dict(self):
        return {
            "round": self.round,
            "current_player_index": getattr(self, "current_player_index", 0),
            "turn_started": getattr(self, "turn_started", False),
            "last_roll": getattr(self, "last_roll", None),
            "current_tile_name": getattr(self, "current_tile_name", None),

            "players": [
                {
                    "name": p.name,
                    "money": p.money,
                    "position": p.position,
                    "resources": p.resources,
                    "skip_turns": getattr(p, "skip_turns", 0),
                    "color": getattr(p, "color", None),
                }
                for p in self.players
            ],

            "board": [
                {
                    "name": t.name,
                    "type": t.type,
                    "price": getattr(t, "price", None),
                    "rent": getattr(t, "rent", None),
                    "owner": getattr(t, "owner", None),
                    "buildings": getattr(t, "buildings", []),
                }
                for t in self.board
            ],
        }