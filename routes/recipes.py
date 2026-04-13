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
        recipes.append({
            "recipe_name": request.form["recipe_name"],
            "ingredients": [],
            "steps": []
        })

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