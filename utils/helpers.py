import json

def has_ingredients_for_recipe(recipe):
    with open("data/sample_food.json") as f:
        data = json.load(f)

    inventory_names = [
        item["product"]["name"].lower()
        for item in data.get("items", [])
    ]

    missing = []

    for ing in recipe.get("ingredients", []):
        name = ing["name"].lower()
        if not any(inv in name or name in inv for inv in inventory_names):
            missing.append(ing["name"])

    return len(missing) == 0, missing

def get_target_user(data, session_user):
    role = session_user.get("role", "").lower()

    if role == "caretaker":
        return next(
            (u for u in data.get("elderly_users", [])
             if u.get("caretaker_id") == session_user["id"]),
            None
        )

    elif role == "elderly":
        return next(
            (u for u in data.get("elderly_users", [])
             if u["id"] == session_user["id"]),
            None
        )

    return None