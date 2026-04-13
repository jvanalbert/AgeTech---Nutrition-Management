from flask import Blueprint, render_template, request, redirect
from Backend.user_loader import load_user_data, save_user_data, username_exists
from extensions import bcrypt

register_bp = Blueprint("register", __name__)

@register_bp.route("/register")
def register():
    return render_template("register.html")

@register_bp.route("/register/elderly", methods=["GET", "POST"])
def register_elderly():
    if request.method == "POST":
        username = request.form["username"]
        if username_exists(username):
            return "Username already exists"

        data = load_user_data()
        new_id = max([e["id"] for e in data.get("elderly_users", [])] + [0]) + 1

        new_elderly = {
            "id": new_id,
            "role": "elderly",
            "name": f"{request.form['first_name']} {request.form['last_name']}",
            "age": int(request.form["age"]),
            "weight_lbs": int(request.form["weight_lbs"]),
            "height_in": int(request.form["height_in"]),
            "medications": [m.strip() for m in request.form["medications"].split(",") if m],
            "allergies": [a.strip() for a in request.form["allergies"].split(",") if a],
            "dietary_restrictions": [d.strip() for d in request.form["dietary_restrictions"].split(",") if d],
            "daily_calories": 1800,
            "cooking_skill": int(request.form["cooking_skill"]),
            "preferred_cuisines": request.form.getlist("cuisines"),
            "meal_times": {
                "breakfast": {"hour": int(request.form["breakfast_hour"]), "minute": int(request.form["breakfast_minute"])},
                "lunch": {"hour": int(request.form["lunch_hour"]), "minute": int(request.form["lunch_minute"])},
                "dinner": {"hour": int(request.form["dinner_hour"]), "minute": int(request.form["dinner_minute"])}
            },
            "account": {"username": username, "password": bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')},
            "contact_information": {"phone": request.form["phone"], "email": request.form["email"]},
            "caretaker_id": None
        }

        data.setdefault("elderly_users", []).append(new_elderly)
        save_user_data(data)
        return redirect("/login")

    return render_template("register_elderly.html")


@register_bp.route("/register/caretaker", methods=["GET", "POST"])
def register_caretaker():
    data = load_user_data()
    elderly_users = data.get("elderly_users", [])

    if request.method == "POST":
        username = request.form["username"]
        if username_exists(username):
            return "Username already exists"

        selected_elderly_ids = [int(eid) for eid in request.form.getlist("elderly_ids")]
        new_id = max([c["id"] for c in data.get("caretaker_users", [])] + [99]) + 1

        new_caretaker = {
            "id": new_id,
            "name": request.form["name"],
            "association": request.form["association"],
            "account": {"username": username, "password": bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')},
            "contact_information": {"phone": request.form["phone"], "email": request.form["email"]},
            "elderly_user_ids": selected_elderly_ids
        }

        data.setdefault("caretaker_users", []).append(new_caretaker)

        for elderly in data["elderly_users"]:
            if elderly["id"] in selected_elderly_ids:
                elderly["caretaker_id"] = new_id

        save_user_data(data)
        return redirect("/login")

    return render_template("register_caretaker.html", elderly_users=elderly_users)