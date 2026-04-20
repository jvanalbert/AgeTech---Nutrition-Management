from flask import Blueprint, render_template, request, redirect, session, url_for
from Backend.scanner import lookup_product, add_item_to_inventory
from Backend.user_loader import load_user_data
import json
from datetime import datetime

foods_bp = Blueprint("foods", __name__)

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

@foods_bp.route("/foods", methods=["GET", "POST"])
def foods():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    target_user = get_target_user(data, session_user)

    if not target_user:
        return redirect("/login")

    message = None
    product = None
    scanned_at = None

    if request.method == "POST":
        barcode = request.form.get("barcode")
        product = lookup_product(barcode)

        if product:
            add_item_to_inventory(barcode, product)
            scanned_at = datetime.now().isoformat()
            message = f"Added {product['name']}"
        else:
            message = "Product not found."

    with open("data/sample_food.json") as f:
        foods = json.load(f).get("items", [])

    return render_template(
        "foods.html",
        foods=foods,
        message=message,
        product=product,
        scanned_at=scanned_at,
        viewer=session_user,
        user=target_user
    )


@foods_bp.post("/foods/<int:food_id>/delete")
def delete_food(food_id):
    with open("data/sample_food.json") as f:
        data = json.load(f)

    data["items"] = [i for i in data["items"] if int(i.get("id", -1)) != food_id]

    with open("data/sample_food.json", "w") as f:
        json.dump(data, f, indent=4)

    return redirect(url_for("foods.foods"))