BUILDINGS = {
    "apartment": {
        "name": "Apartment Complex",
        "cost_money": 200,
        "cost_resources": {
            "materials": 2,
            "labor": 2,
            "energy": 0,
            "commerce": 0,
            "infrastructure": 1,
        },
        "effect": "rent_bonus",
        "rent_multiplier": 1.5,
        "resource_output": {
            "commerce": 1,
        },
    },
    "factory": {
        "name": "Factory",
        "cost_money": 250,
        "cost_resources": {
            "materials": 3,
            "labor": 2,
            "energy": 2,
            "commerce": 0,
            "infrastructure": 1,
        },
        "effect": "materials_income",
        "resource_output": {
            "materials": 2,
            "commerce": 1,
        },
        "rent_multiplier": 0.8,
    },
    "power_plant": {
        "name": "Power Plant",
        "cost_money": 220,
        "cost_resources": {
            "materials": 2,
            "labor": 1,
            "energy": 0,
            "commerce": 0,
            "infrastructure": 1,
        },
        "effect": "energy_income",
        "resource_output": {
            "energy": 2,
        },
        "rent_multiplier": 1.0,
    },
    "mall": {
        "name": "Mall",
        "cost_money": 300,
        "cost_resources": {
            "materials": 2,
            "labor": 2,
            "energy": 1,
            "commerce": 1,
            "infrastructure": 1,
        },
        "effect": "commerce_income",
        "resource_output": {
            "commerce": 2,
        },
        "rent_multiplier": 1.8,
    },
    "construction_hub": {
        "name": "Construction Hub",
        "cost_money": 260,
        "cost_resources": {
            "materials": 2,
            "labor": 2,
            "energy": 1,
            "commerce": 0,
            "infrastructure": 0,
        },
        "effect": "infrastructure_income",
        "resource_output": {
            "infrastructure": 2,
        },
        "rent_multiplier": 1.0,
    },
}