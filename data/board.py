from models.tile import Tile


def create_board():
    return [
        Tile("Start", "start"),

        Tile("Mladost", "region", 400, 100, "labor", production_number=6),
        Tile("Event", "event"),
        Tile("Vitosha", "region", 350, 90, "energy", production_number=8),

        Tile("Tax", "tax"),
        Tile("Central Capitol", "region", 450, 120, "commerce", production_number=5),
        Tile("Event", "event"),
        Tile("Lulin", "region", 300, 75, "labor", production_number=9),

        Tile("PEC District", "region", 320, 80, "commerce", production_number=4),
        Tile("Event", "event"),
        Tile("Airport District", "region", 360, 85, "infrastructure", production_number=10),

        Tile("Tax", "tax"),
        Tile("Government District", "region", 500, 130, "commerce", production_number=3),
        Tile("Ovcha Kupel", "region", 300, 75, "labor", production_number=11),

        Tile("Event", "event"),
        Tile("Krasna Polyana", "region", 280, 70, "labor", production_number=2),
        Tile("Vladaya", "region", 260, 65, "materials", production_number=12),

        Tile("Boyana", "region", 340, 85, "energy", production_number=7),
        Tile("Bankya", "region", 250, 60, "labor", production_number=6),

        Tile("Pernik", "region", 300, 75, "materials", production_number=8),
        Tile("Mihaylovgrad", "region", 300, 75, "materials", production_number=5),

        Tile("Novi Han", "region", 280, 70, "materials", production_number=9),
        Tile("Sapareva Banya", "region", 250, 60, "labor", production_number=4),

        Tile("Vranevo", "region", 350, 0, "energy", production_number=10),
        Tile("Bansko", "region", 250, 60, "energy", production_number=3),

        Tile("Varna", "region", 350, 90, "commerce", production_number=11),
        Tile("Tarnovo", "region", 320, 80, "commerce", production_number=2),
        Tile("Customs Checkpoint", "tax"),
    ]