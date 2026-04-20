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

    session_user = session["user"]
    data = load_user_data()

    target_user = get_target_user(data, session_user)

    # 🚫 BLOCK CARETAKERS (since you said you want this hidden entirely)
    if session_user.get("role") == "caretaker":
        return redirect("/home")

    with open("data/saved_recipes.json") as f:
        recipes = json.load(f).get("recipes", [])

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