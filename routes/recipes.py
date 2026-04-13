from flask import Blueprint, render_template, request, redirect, session, url_for
import json
from Backend.recipe import generate_recipe

recipes_bp = Blueprint("recipes", __name__)

FILE = "data/saved_recipes.json"

@recipes_bp.route("/recipes", methods=["GET", "POST"])
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
        recipes=data.get("recipes", []),
        generated_recipe=generated
    )