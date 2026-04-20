from flask import Blueprint, render_template, session, redirect
from Backend.user_loader import load_user_data
import json

recipes_bp = Blueprint("recipes", __name__)


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


@recipes_bp.route("/recipes")
def recipes():
    if not session.get("user"):
        return redirect("/login")

    with open(FILE) as f:
        data = json.load(f)

    recipes = data.get("recipes", [])

    if request.method == "POST":
        time_value = request.form.get("estimated_time_value", 0)
        time_unit = request.form.get("estimated_time_unit", "min")

        try:
            time_value = int(time_value)
        except:
            time_value = 0

        if time_unit == "hours":
            estimated_time_minutes = time_value * 60
        else:
            estimated_time_minutes = time_value
        
        new_recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "servings": int(request.form.get("servings", 1)),
            "ingredients": [],
            "steps": [],
            "estimated_time_minutes": estimated_time_minutes
        }

        # 🔹 Ingredients (multi-row fix)
        names = request.form.getlist("ingredient_name")
        amounts = request.form.getlist("ingredient_amount")
        units = request.form.getlist("ingredient_unit")

        for i in range(len(names)):
            if names[i] and names[i].strip():
                new_recipe["ingredients"].append({
                    "amount": amounts[i],
                    "unit": units[i],
                    "name": names[i]
                })

        # 🔹 Steps fix
        steps_text = request.form.get("steps", "").strip()
        if steps_text:
            new_recipe["steps"] = [
                s.strip() for s in steps_text.splitlines() if s.strip()
            ]

        # 🔹 Save
        recipes.append(new_recipe)

        with open(FILE, "w") as f:
            json.dump({"recipes": recipes}, f, indent=4)

        return redirect("/recipes")

    return render_template("recipes.html", recipes=recipes)


@recipes_bp.post("/recipes/<int:index>/delete")
def delete_recipe(index):
    with open(FILE) as f:
        data = json.load(f)

    recipes = data.get("recipes", [])

    if 0 <= index < len(recipes):
        recipes.pop(index)

    with open(FILE, "w") as f:
        json.dump({"recipes": recipes}, f, indent=4)

    return redirect(url_for("recipes.recipes"))

@recipes_bp.post("/recipes/update")
def update_recipe():
    index = int(request.form.get("index"))

    with open(FILE) as f:
        data = json.load(f)

    recipes = data.get("recipes", [])

    if index < 0 or index >= len(recipes):
        return redirect(url_for("recipes.recipes"))

    # time
    value = int(request.form.get("estimated_time_value", 0))
    unit = request.form.get("estimated_time_unit", "min")
    minutes = value * 60 if unit == "hours" else value

    updated = {
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
            updated["ingredients"].append({
                "amount": amounts[i],
                "unit": units[i],
                "name": names[i]
            })

    # steps
    steps_text = request.form.get("steps", "")
    updated["steps"] = [s.strip() for s in steps_text.split("\n") if s.strip()]

    recipes[index] = updated

    with open(FILE, "w") as f:
        json.dump({"recipes": recipes}, f, indent=4)

    return redirect(url_for("recipes.recipes"))


@recipes_bp.route("/generate_recipe", methods=["POST"])
def generate_recipe_route():
    meal_type = request.form.get("meal_type", "dinner")

    try:
        raw = generate_recipe(meal_type)

        if raw.startswith("```"):
            raw = raw.strip("`").replace("json\n", "")

        generated = json.loads(raw)
    except:
        generated = None

    with open(FILE) as f:
        data = json.load(f)

    return render_template(
        "recipes.html",
        recipes=recipes,
        user=target_user,
        viewer=session_user   # 👈 THIS FIXES YOUR ERROR
    )

@recipes_bp.route("/delete_recipe", methods=["POST"])
def delete_recipe():
    if not session.get("user"):
        return redirect("/login")

    index = request.form.get("index")

    # load recipes
    import json
    with open("data/saved_recipes.json") as f:
        data = json.load(f)

    if "recipes" in data and index is not None:
        try:
            index = int(index)
            if 0 <= index < len(data["recipes"]):
                data["recipes"].pop(index)

                with open("data/saved_recipes.json", "w") as f:
                    json.dump(data, f, indent=4)
        except:
            pass

    return redirect(url_for("recipes.recipes"))