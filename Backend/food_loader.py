# food_loader.py
import json

def load_foods(path="data/sample_food.json"):
    """
    Load foods from sample_food.json
    Returns a simplified list of foods usable by meal generator.
    """
    with open(path, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    foods = []
    food_id = 1

    for item in inventory.get("items", []):
        product = item["product"]

        foods.append({
            "id": food_id,
            "name": product["name"],
            "calories": product["calories"],
            "category": product["category"]
        })
        food_id += 1

    return foods
