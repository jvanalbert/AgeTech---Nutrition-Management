from flask import Blueprint, render_template, session, redirect, request
from Backend.user_loader import load_user_data, save_user_data
from Backend.food_loader import load_foods
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
            "protein": float(food.get("protein", 0)),
            "cholesterol": float(food.get("cholesterol", 0)),
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
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    todays_meals = [
        m for m in target_user.get("meals", []) 
        if m.get("date") == today_str
    ]

    return render_template(
        "meals.html",
        foods=foods,
        user_meals=todays_meals,
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

# from flask import Blueprint, render_template, session, redirect, request
# from Backend.user_loader import load_user_data, save_user_data
# from Backend.food_loader import load_foods
# from utils.helpers import has_ingredients_for_recipe
# import json
# from datetime import datetime

# meals_bp = Blueprint("meals", __name__)

# @meals_bp.route("/meals", methods=["GET", "POST"])
# def meals():
#     if not session.get("user"):
#         return redirect("/login")

#     data = load_user_data()
#     user_id = session["user"]["id"]

#     user = next((u for u in data["elderly_users"] if u["id"] == user_id), None)
#     user_meals = user.get("meals", []) if user else []

#     foods = load_foods()

#     # 🔹 ADD MEAL
#     if request.method == "POST":
#         food_id = int(request.form["food_id"])
#         quantity = float(request.form["quantity"])
#         meal_type = request.form["meal_type"]

#         food = next((f for f in foods if f["id"] == food_id), None)
#         if not food:
#             return redirect("/meals")

#         meal = {
#             "food_id": food_id,
#             "name": food["name"],
#             "quantity": quantity,
#             "meal_type": meal_type,
#             "calories": float(food.get("calories", 0)),
#             "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")
#         }

#         user.setdefault("meals", []).append(meal)
#         save_user_data(data)

#         return redirect("/meals")

#     # 🔹 LOAD RECIPES
#     with open("data/saved_recipes.json") as f:
#         recipe_data = json.load(f)

#     recipes = recipe_data.get("recipes", [])

#     recipe_availability = []
#     for recipe in recipes:
#         has_all, missing = has_ingredients_for_recipe(recipe)
#         recipe_availability.append({
#             "recipe": recipe,
#             "has_all": has_all,
#             "missing": missing
#         })

#     return render_template(
#         "meals.html",
#         foods=foods,
#         user_meals=user_meals,
#         recipes=recipes,
#         recipe_availability=recipe_availability
#     )


# @meals_bp.post("/delete_meal")
# def delete_meal():
#     if not session.get("user"):
#         return redirect("/login")

#     timestamp = request.form["timestamp"]

#     data = load_user_data()
#     user_id = session["user"]["id"]

#     user = next((u for u in data["elderly_users"] if u["id"] == user_id), None)

#     if user:
#         user["meals"] = [m for m in user.get("meals", []) if m["timestamp"] != timestamp]
#         save_user_data(data)

#     return redirect("/meals")