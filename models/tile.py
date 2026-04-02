from data.buildings import BUILDINGS


class Tile:
    def __init__(self, name, tile_type, price=0, rent=0, resource=None, production_number=None):
        self.name = name
        self.type = tile_type
        self.price = price
        self.base_rent = rent
        self.owner = None
        self.level = 0
        self.resource = resource
        self.buildings = []
        self.production_number = production_number

    def get_rent(self):
        rent = int(self.base_rent * (1 + 0.5 * self.level))

        for building_key in self.buildings:
            building = BUILDINGS[building_key]
            multiplier = building.get("rent_multiplier", 1.0)
            rent = int(rent * multiplier)

        return max(rent, 0)