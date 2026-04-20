from flask import Blueprint, render_template, session, redirect, request, url_for
from Backend.user_loader import load_user_data
import json

recipes_bp = Blueprint("recipes", __name__)

FILE = "data/saved_recipes.json"


# =========================
# USER CONTEXT
# =========================
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


# =========================
# MAIN RECIPES PAGE
# =========================
@recipes_bp.route("/recipes", methods=["GET", "POST"])
def recipes():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    target_user = get_target_user(data, session_user)

    with open(FILE) as f:
        file_data = json.load(f)

    recipes_list = file_data.get("recipes", [])

    # =====================
    # ADD RECIPE
    # =====================
    if request.method == "POST":

        time_value = request.form.get("estimated_time_value", 0)
        time_unit = request.form.get("estimated_time_unit", "min")

        try:
            time_value = int(time_value)
        except:
            time_value = 0

        estimated_time_minutes = time_value * 60 if time_unit == "hours" else time_value

        new_recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "servings": int(request.form.get("servings", 1)),
            "ingredients": [],
            "steps": [],
            "estimated_time_minutes": estimated_time_minutes
        }

        names = request.form.getlist("ingredient_name")
        amounts = request.form.getlist("ingredient_amount")
        units = request.form.getlist("ingredient_unit")

        for i in range(len(names)):
            if names[i].strip():
                new_recipe["ingredients"].append({
                    "amount": amounts[i],
                    "unit": units[i],
                    "name": names[i]
                })

        steps_text = request.form.get("steps", "")
        new_recipe["steps"] = [s.strip() for s in steps_text.splitlines() if s.strip()]

        recipes_list.append(new_recipe)

        with open(FILE, "w") as f:
            json.dump({"recipes": recipes_list}, f, indent=4)

        return redirect("/recipes")

    return render_template(
        "recipes.html",
        recipes=recipes_list,
        user=target_user,
        viewer=session_user
    )

@recipes_bp.post("/recipes/update")
def update_recipe():
    if not session.get("user"):
        return redirect("/login")

    index = int(request.form.get("index"))

    with open(FILE) as f:
        data = json.load(f)

    recipes_list = data.get("recipes", [])

    # safety check
    if index < 0 or index >= len(recipes_list):
        return redirect(url_for("recipes.recipes"))

    # time conversion
    value = int(request.form.get("estimated_time_value", 0))
    unit = request.form.get("estimated_time_unit", "min")
    minutes = value * 60 if unit == "hours" else value

    # rebuild recipe
    updated_recipe = {
        "recipe_name": request.form.get("recipe_name"),
        "servings": int(request.form.get("servings", 1)),
        "ingredients": [],
        "steps": [],
        "estimated_time_minutes": minutes
    }

    # ingredients
    names = request.form.getlist("ingredient_name")
    amounts = request.form.getlist("ingredient_amount")
    units = request.form.getlist("ingredient_unit")

    for i in range(len(names)):
        if names[i].strip():
            updated_recipe["ingredients"].append({
                "amount": amounts[i],
                "unit": units[i],
                "name": names[i]
            })

    # steps
    steps_text = request.form.get("steps", "")
    updated_recipe["steps"] = [s.strip() for s in steps_text.splitlines() if s.strip()]

    # replace recipe
    recipes_list[index] = updated_recipe

    # save
    with open(FILE, "w") as f:
        json.dump({"recipes": recipes_list}, f, indent=4)

    return redirect(url_for("recipes.recipes"))

# =========================
# DELETE RECIPE (FIXED ONCE)
# =========================
@recipes_bp.post("/recipes/<int:index>/delete")
def delete_recipe(index):
    if not session.get("user"):
        return redirect("/login")

    with open(FILE) as f:
        data = json.load(f)

    recipes_list = data.get("recipes", [])

    if 0 <= index < len(recipes_list):
        recipes_list.pop(index)

    with open(FILE, "w") as f:
        json.dump({"recipes": recipes_list}, f, indent=4)

    return redirect(url_for("recipes.recipes"))


# =========================
# GENERATE RECIPE
# =========================
@recipes_bp.route("/generate_recipe", methods=["POST"])
def generate_recipe_route():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()
    target_user = get_target_user(data, session_user)

    meal_type = request.form.get("meal_type", "dinner")

    try:
        raw = generate_recipe(meal_type)

        if raw.startswith("```"):
            raw = raw.strip("`").replace("json\n", "")

        generated = json.loads(raw)
    except:
        generated = None

    with open(FILE) as f:
        file_data = json.load(f)

    return render_template(
        "recipes.html",
        recipes=file_data.get("recipes", []),
        generated_recipe=generated,
        user=target_user,
        viewer=session_user
    )