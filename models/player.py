class Player:
    def __init__(self, name: str):
        self.name = name
        self.money = 1000
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.skip_turns = 0
        self.color = None

        self.resources = {
            "materials": 0,
            "energy": 0,
            "labor": 0,
            "commerce": 0,
            "infrastructure": 0,
        }

    def __repr__(self):
        return f"{self.name} (${self.money})"