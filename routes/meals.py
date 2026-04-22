from flask import Blueprint, render_template, session, redirect, request
from Backend.user_loader import load_user_data, save_user_data
from Backend.food_loader import load_foods
from Backend.recipe import generate_recipe
from utils.helpers import has_ingredients_for_recipe
import json
from datetime import datetime

meals_bp = Blueprint("meals", __name__)


# =========================
# HELPERS
# =========================
def get_target_user(data, session_user):
    """Returns the elderly user being viewed (caretaker or self)."""

    if session_user.get("role") == "caretaker":
        for u in data.get("elderly_users", []):
            if u.get("caretaker_id") == session_user["id"]:
                return u

    elif session_user.get("role") == "elderly":
        return next(
            (u for u in data.get("elderly_users", []) if u["id"] == session_user["id"]),
            None
        )

    return None


# =========================
# MEALS PAGE
# =========================
@meals_bp.route("/meals", methods=["GET", "POST"])
def meals():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    target_user = get_target_user(data, session_user)

    if not target_user:
        return redirect("/login")

    foods = load_foods()

    # =====================
    # ADD FOOD MEAL
    # =====================
    if request.method == "POST":
        food_id = int(request.form["food_id"])
        quantity = float(request.form["quantity"])
        meal_type = request.form["meal_type"]

        food = next((f for f in foods if f["id"] == food_id), None)
        if not food:
            return redirect("/meals")

        meal = {
            "food_id": food_id,
            "name": food["name"],
            "quantity": quantity,
            "meal_type": meal_type,
            "calories": float(food.get("calories", 0)),
            "sugar": float(food.get("sugar", 0)),
            "sodium": float(food.get("sodium", 0)),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
            "allergens": food.get("allergens", [])
        }

        target_user.setdefault("meals", []).append(meal)
        save_user_data(data)

        return redirect("/meals")

    # =====================
    # LOAD RECIPES
    # =====================
    with open("data/saved_recipes.json") as f:
        recipe_data = json.load(f)

    recipes = recipe_data.get("recipes", [])

    recipe_availability = []
    for recipe in recipes:
        has_all, missing = has_ingredients_for_recipe(recipe)
        recipe_availability.append({
            "recipe": recipe,
            "has_all": has_all,
            "missing": missing
        })

    return render_template(
        "meals.html",
        foods=foods,
        user_meals=target_user.get("meals", []),
        recipes=recipes,
        recipe_availability=recipe_availability,
        viewer=session_user,
        user=target_user
    )


# =========================
# DELETE MEAL
# =========================
@meals_bp.post("/delete_meal")
def delete_meal():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    target_user = get_target_user(data, session_user)

    if not target_user:
        return redirect("/meals")

    timestamp = request.form["timestamp"]

    target_user["meals"] = [
        m for m in target_user.get("meals", [])
        if m["timestamp"] != timestamp
    ]

    save_user_data(data)

    return redirect("/meals")

@meals_bp.route("/generate_recipe", methods=["POST"])
def generate_recipe_route():
    if not session.get("user"):
        return redirect("/login")

    # Load user data (same as /meals)
    session_user = session["user"]
    data = load_user_data()
    user_id = session["user"]["id"]
    user = None

    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break

    user_meals = user.get("meals", []) if user else []

    foods = load_foods()

    # ✅ FILTER FOODS (same as your route)
    user_allergies = []
    if user:
        user_allergies = user.get("allergies", [])
        filtered_foods = []

        for f in foods:
            safe = True
            for allergen in user_allergies:
                for a in f.get("allergens", []):
                    if allergen.lower() == a.lower():
                        safe = False
                        break
                if not safe:
                    break
            if safe:
                filtered_foods.append(f)

        foods = filtered_foods

    # ✅ LOAD SAVED RECIPES (same as your route)
    with open("data/saved_recipes.json") as f:
        recipe_data = json.load(f)

    recipes = recipe_data.get("recipes", [])

    recipe_availability = []
    for recipe in recipes:
        has_all, missing = has_ingredients_for_recipe(recipe)
        recipe_availability.append({
            "recipe": recipe,
            "has_all": has_all,
            "missing": missing
        })

    # 🔥 NEW: GENERATE AI RECIPE
    meal_type = request.form.get("meal_type", "dinner")
    recipe_json = generate_recipe(meal_type)

    try:
        recipe_json = generate_recipe(meal_type)

        print("RAW AI RESPONSE:")
        print(recipe_json)

        # 🔥 REMOVE ```json and ```
        if recipe_json.startswith("```"):
            recipe_json = recipe_json.strip("`")          # remove backticks
            recipe_json = recipe_json.replace("json\n", "")  # remove 'json\n'

        generated_recipe = json.loads(recipe_json)

    except Exception as e:
        print("AI ERROR:", e)
        print("CLEANED RESPONSE:", recipe_json)
        generated_recipe = None

    # ✅ RETURN SAME TEMPLATE + ONE EXTRA VARIABLE
    return render_template(
    "meals.html",
    foods=foods,
    user_meals=user_meals,
    user_allergies=user_allergies,
    recipes=recipes,
    recipe_availability=recipe_availability,
    generated_recipe=generated_recipe,
    viewer=session_user,   # ✅ ADD THIS
    user=user              # ✅ ADD THIS
)

@meals_bp.post("/log_recipe_meal")
def log_recipe_meal():
    if not session.get("user"):
        return redirect("/login")

    recipe_index = int(request.form["recipe_index"])
    meal_type = request.form.get("meal_type", "dinner")

    # Load recipes
    with open("data/saved_recipes.json") as f:
        data = json.load(f)

    recipes = data.get("recipes", [])

    if recipe_index >= len(recipes):
        return redirect("/meals")

    recipe = recipes[recipe_index]

    # Check ingredients
    has_all, missing = has_ingredients_for_recipe(recipe)

    if not has_all:
        return f"Missing ingredients: {', '.join(missing)} <br><a href='/meals'>Go back</a>"

    meal = {
        "name": recipe["recipe_name"],
        "meal_type": meal_type,
        "calories": 0,
        "protein": 0,
        "sodium": 0,
        "sugar": 0,
        "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
        "ingredients": recipe["ingredients"]
    }

    data = load_user_data()
    user_id = session["user"]["id"]

    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            u.setdefault("meals", []).append(meal)
            break

    save_user_data(data)

    return redirect("/meals")

@meals_bp.post("/log_generated_meal")
def log_generated_meal():
    if not session.get("user"):
        return redirect("/login")

    import json
    from datetime import datetime

    # Parse recipe safely
    try:
        recipe = json.loads(request.form.get("recipe_json", "{}"))
    except Exception:
        return redirect("/meals")

    meal_type = request.form.get("meal_type", "dinner")

    # Build meal safely (AI may miss fields)
    meal = {
        "name": recipe.get("recipe_name", "Generated Meal"),
        "meal_type": meal_type,
        "calories": recipe.get("calories", 0),
        "protein": recipe.get("protein", 0),
        "sodium": recipe.get("sodium", 0),
        "sugar": recipe.get("sugar", 0),
        "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
        "ingredients": recipe.get("ingredients", [])
    }

    # Load users
    data = load_user_data()
    user_id = session["user"]["id"]

    # Find user safely
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u.get("id") == user_id:
            u.setdefault("meals", []).append(meal)
            break

    save_user_data(data)

    return redirect("/meals")