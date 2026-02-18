# app.py
from flask import Flask, render_template, request, redirect, session, url_for
from flask_bcrypt import Bcrypt
from datetime import datetime
from Backend.food_loader import load_foods
from Backend.user_loader import (
    load_user_data,
    save_user_data,
    load_elderly_users,
    username_exists,
    load_elderly_users_with_caretakers
)
from Backend.scanner import lookup_product, add_item_to_inventory

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "supersecretkey"  # Required for sessions. Change in production.

# ------------------ Helper functions ------------------
def check_login(username, password):
    """Return user dict if credentials match, else None."""
    data = load_user_data()
    for user in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if user["account"]["username"] == username and bcrypt.check_password_hash(user["account"]["password"], password):
            return user
    return None

# ------------------ Routes ------------------

@app.route("/")
def root():
    # If already logged in, go to home
    if session.get("user"):
        return redirect("/home")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = check_login(username, password)
        if user:
            session["user"] = {
                "id": user["id"],
                "role": user.get("role", "elderly"),
                "name": user.get("name")
            }
            return redirect("/home")
        else:
            return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


@app.route("/register/elderly", methods=["GET", "POST"])
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
            "account": {"username": username, "password": bcrypt.generate_password_hash(request.form["password"]).decode('utf-8')},
            "contact_information": {"phone": request.form["phone"], "email": request.form["email"]},
            "caretaker_id": None
        }

        data.setdefault("elderly_users", []).append(new_elderly)
        save_user_data(data)
        return redirect("/login")

    return render_template("register_elderly.html")


@app.route("/register/caretaker", methods=["GET", "POST"])
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


@app.route("/home")
def home():
    if not session.get("user"):
        return redirect("/login")
    return render_template("home.html", user=session["user"])


@app.route("/users")
def users_page():
    if not session.get("user"):
        return redirect("/login")
    elderly_users = load_elderly_users_with_caretakers()
    return render_template("users.html", users=elderly_users)


@app.get("/foods")
def food_list():
    if not session.get("user"):
        return redirect("/login")

    import json
    with open("data/sample_food.json", "r") as f:
        data = json.load(f)

    foods = data.get("items", [])
    print("FOODS IDS:", [item.get("id") for item in foods][:20])
    return render_template("foods.html", foods=foods)



# Delete
@app.post("/foods/<int:food_id>/delete")
def delete_food(food_id):
    if not session.get("user"):
        return redirect("/login")

    import json

    # Load data
    with open("data/sample_food.json", "r") as f:
        data = json.load(f)

    # Filter out the matching id
    data["items"] = [
        item for item in data.get("items", [])
        if int(item.get("id", -1)) != food_id
    ]

    # Save updated data
    with open("data/sample_food.json", "w") as f:
        json.dump(data, f, indent=4)

    return redirect(url_for("food_list"))


@app.route("/scan", methods=["GET", "POST"])
def scan():
    if not session.get("user"):
        return redirect("/login")
    
    if request.method == "POST":
        barcode = request.form["barcode"]
        product = lookup_product(barcode)
        if product:
            add_item_to_inventory(barcode, product)
            scanned_at = datetime.now().isoformat()
            return render_template("scan.html", message=f"Added {product['name']} to inventory.", product=product, scanned_at=scanned_at)
        else:
            return render_template("scan.html", message="Product not found.")
    
    return render_template("scan.html")

@app.route("/meals", methods=["GET", "POST"])
def meals():
    if not session.get("user"):
        return redirect("/login")
    
    # Load user data to get meals
    data = load_user_data()
    user_id = session["user"]["id"]
    user = None #gives none if not found
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break
    user_meals = user.get("meals", []) if user else []
    
    if request.method == "POST":
        food_id = int(request.form["food_id"])
        quantity = float(request.form["quantity"])
        meal_type = request.form["meal_type"]
        
        if user:
            # Get food data
            foods = load_foods()
            food = next((f for f in foods if f["id"] == food_id), None)
            
            if food:
                meal = {
                    "food_id": food_id,
                    "name": food["name"],
                    "quantity": quantity,
                    "meal_type": meal_type,
                    "calories": food["calories"] * quantity / 100,  # assuming per 100g like taylor said
                    "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M %p"),  #date/time format
                    "allergens": food.get("allergens", [])
                }
                user["meals"] = user.get("meals", []) + [meal]
                save_user_data(data)
                return redirect("/meals")
    
    foods = load_foods()
    # Filter foods based on user allergies
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
    return render_template("meals.html", foods=foods, user_meals=user_meals, user_allergies=user_allergies)


@app.route("/delete_meal", methods=["POST"])
def delete_meal():
    if not session.get("user"):
        return redirect("/login")
    
    timestamp = request.form["timestamp"]
    
    data = load_user_data()
    user_id = session["user"]["id"]
    user = None
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break
    
    if user and "meals" in user:
        user["meals"] = [m for m in user["meals"] if m["timestamp"] != timestamp]
        save_user_data(data)
    
    return redirect("/meals")


# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True)
