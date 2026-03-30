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
import json
from pathlib import Path

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

def has_ingredients_for_recipe(recipe):
    import json

    # Load inventory
    with open("data/sample_food.json") as f:
        data = json.load(f)

    inventory_items = data.get("items", [])

    # Normalize inventory names
    inventory_names = [
        item["product"]["name"].lower()
        for item in inventory_items
    ]

    missing = []

    for ing in recipe.get("ingredients", []):
        ing_name = ing["name"].lower()

        # Check if ANY inventory item matches (partial match)
        found = any(inv_name in ing_name or ing_name in inv_name for inv_name in inventory_names)

        if not found:
            missing.append(ing["name"])

    return len(missing) == 0, missing

# nutrition helpers

# tracks calories based on a 2000 calorie diet
def track_calories(user):
    goal = user.get("daily_calories", 2000)
    meals = user.get("meals", [])

    consumed = sum(meal.get("calories", 0) for meal in meals)
    remaining = goal - consumed

    return {
        "goal": goal,
        "consumed": consumed,
        "remaining": remaining
    }

# determines protein by body weight (lbs x 1.2)
def get_protein_goal(user):
    weight = user.get("weight_lbs", 0)
    protein_goal = weight * 1.2
    return round(protein_goal, 1)

# tracks protein for user
def track_protein(user):
    goal = get_protein_goal(user)
    meals = user.get("meals", [])

    consumed = sum(meal.get("protein", 0) for meal in meals)
    remaining = goal - consumed

    return {
        "goal": goal,
        "consumed": consumed,
        "remaining": remaining
    }

# cholestrol for user
def get_cholesterol_goal(user):
    medications = user.get("medications", [])
    medications_lower = [med.lower() for med in medications]

    # high cholestrol medications (note: exhaust the list and add more)
    stricter_goal_meds = ["Statins", "Atorvastatin", "Rosuvastatin", "Simvastatin", "Pravastatin",
    "Lovastatin", "Fluvastatin", "Pitavastatin"]

    # 300 for normal cholestrol, 200 if high cholestrol 
    if any(med in medications_lower for med in stricter_goal_meds):
        return 200
    return 300

def track_cholesterol(user):
    goal = get_cholesterol_goal(user)
    meals = user.get("meals", [])

    consumed = sum(meal.get("cholesterol", 0) for meal in meals)
    remaining = goal - consumed

    return {
        "goal": goal,
        "consumed": consumed,
        "remaining": remaining
    }

# if male -> 36 g, female -> 25 g
def get_sugar_goal(user):
    gender = user.get("gender", "").lower()

    if gender == "male":
        return 36
    return 25

def track_sugar(user):
    goal = get_sugar_goal(user)
    meals = user.get("meals", [])

    consumed = sum(meal.get("sugar", 0) for meal in meals)
    remaining = goal - consumed

    return {
        "goal": goal,
        "consumed": consumed,
        "remaining": remaining
    }


# 1300 mg for any person over 50
def get_sodium_goal(user):
    return 1300

def track_sodium(user):
    goal = get_sodium_goal(user)
    meals = user.get("meals", [])

    consumed = sum(meal.get("sodium", 0) for meal in meals)
    remaining = goal - consumed

    return {
        "goal": goal,
        "consumed": consumed,
        "remaining": remaining
    }
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
            # Add meal_times to session for elderly users
            if user.get("role") == "elderly":
                session["meal_times"] = user.get("meal_times", {"breakfast": {"hour": 8, "minute": 0}, "lunch": {"hour": 12, "minute": 0}, "dinner": {"hour": 18, "minute": 0}})
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
    
    user = session["user"]
    
    # Get nutrition data if user is elderly
    nutrition_data = None
    if user.get("role") == "elderly":
        data = load_user_data()
        elderly_user = None
        for u in data.get("elderly_users", []):
            if u["id"] == user["id"]:
                elderly_user = u
                break
        
        if elderly_user:
            calorie_totals = track_calories(elderly_user)
            protein_totals = track_protein(elderly_user)
            cholesterol_totals = track_cholesterol(elderly_user)
            sugar_totals = track_sugar(elderly_user)
            sodium_totals = track_sodium(elderly_user)
            
            nutrition_data = {
                "calories": calorie_totals,
                "protein": protein_totals,
                "cholesterol": cholesterol_totals,
                "sugar": sugar_totals,
                "sodium": sodium_totals
            }
    
    return render_template("home.html", user=user, nutrition=nutrition_data)


@app.route("/users")
def users_page():
    if not session.get("user"):
        return redirect("/login")
    elderly_users = load_elderly_users_with_caretakers()
    # Add default meal_times if missing
    for user in elderly_users:
        if "meal_times" not in user:
            user["meal_times"] = {"breakfast": {"hour": 8, "minute": 0}, "lunch": {"hour": 12, "minute": 0}, "dinner": {"hour": 18, "minute": 0}}
    return render_template("users.html", users=elderly_users)


@app.route("/edit_meal_times/<int:user_id>", methods=["GET", "POST"])
def edit_meal_times(user_id):
    if not session.get("user"):
        return redirect("/login")
    
    # Check permissions: caretaker for this user or the user themselves
    data = load_user_data()
    user = None
    for u in data.get("elderly_users", []):
        if u["id"] == user_id:
            user = u
            break
    
    if not user:
        return "User not found", 404
    
    # Permission check
    if session["user"]["role"] == "caretaker":
        if user.get("caretaker_id") != session["user"]["id"]:
            return "Unauthorized", 403
    elif session["user"]["role"] == "elderly":
        if user["id"] != session["user"]["id"]:
            return "Unauthorized", 403
    else:
        return "Unauthorized", 403
    
    if request.method == "POST":
        # Update meal_times
        user["meal_times"] = {
            "breakfast": {"hour": int(request.form["breakfast_hour"]), "minute": int(request.form["breakfast_minute"])},
            "lunch": {"hour": int(request.form["lunch_hour"]), "minute": int(request.form["lunch_minute"])},
            "dinner": {"hour": int(request.form["dinner_hour"]), "minute": int(request.form["dinner_minute"])}
        }
        save_user_data(data)
        # Update session if editing own meal times
        if session["user"]["id"] == user_id:
            session["meal_times"] = user["meal_times"]
        return redirect("/users")
    
    # Add defaults if missing
    meal_times = user.get("meal_times", {"breakfast": {"hour": 8, "minute": 0}, "lunch": {"hour": 12, "minute": 0}, "dinner": {"hour": 18, "minute": 0}})
    return render_template("edit_meal_times.html", user=user, meal_times=meal_times)


@app.route("/caretaker")
def caretaker_page():
    if not session.get("caretaker"):
        return redirect("/login")
    caretaker_users = load_user_data().get("caretaker_users", [])
    return render_template("caretakers.html", caretakers=caretaker_users)


@app.route("/foods", methods=["GET", "POST"])
def food_list():
    if not session.get("user"):
        return redirect("/login")

    import json
    from datetime import datetime

    message = None
    product = None
    scanned_at = None

    # 🔹 Handle scanning
    if request.method == "POST":
        barcode = request.form.get("barcode")
        product = lookup_product(barcode)

        if product:
            add_item_to_inventory(barcode, product)
            scanned_at = datetime.now().isoformat()
            message = f"Added {product['name']} to inventory."
        else:
            message = "Product not found."

    # 🔹 Load foods (same as before)
    with open("data/sample_food.json", "r") as f:
        data = json.load(f)

    foods = data.get("items", [])

    print("FOODS IDS:", [item.get("id") for item in foods][:20])

    return render_template(
        "foods.html",
        foods=foods,
        message=message,
        product=product,
        scanned_at=scanned_at
    )


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

@app.route("/nutrition")
def nutrition():
    if not session.get("user"):
        return redirect("/login")
    
    data = load_user_data()
    user_id = session["user"]["id"]
    user = None
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break
    
    if not user or user.get("role") != "elderly":
        return "Nutrition tracking is only available for elderly users", 403

    calorie_totals = track_calories(user)
    protein_totals = track_protein(user)
    cholesterol_totals = track_cholesterol(user)
    sugar_totals = track_sugar(user)
    sodium_totals = track_sodium(user)

    # Format current date for display
    current_date = datetime.now().strftime("%B %d, %Y")

    return render_template(
        "nutrition.html",
        user=user,
        current_date=current_date,
        goal=calorie_totals["goal"],
        consumed=calorie_totals["consumed"],
        remaining=calorie_totals["remaining"],

        protein_goal=protein_totals["goal"],
        protein_consumed=protein_totals["consumed"],
        protein_remaining=protein_totals["remaining"],

        cholesterol_goal=cholesterol_totals["goal"],
        cholesterol_consumed=cholesterol_totals["consumed"],
        cholesterol_remaining=cholesterol_totals["remaining"],

        sugar_goal=sugar_totals["goal"],
        sugar_consumed=sugar_totals["consumed"],
        sugar_remaining=sugar_totals["remaining"],

        sodium_goal=sodium_totals["goal"],
        sodium_consumed=sodium_totals["consumed"],
        sodium_remaining=sodium_totals["remaining"],




    )



#------- Meal Page -------#
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

    foods = load_foods()
    
    if request.method == "POST":
        food_id = int(request.form["food_id"])
        quantity = float(request.form["quantity"])
        meal_type = request.form["meal_type"]
        unit = request.form.get("unit", "grams")

        # Load foods and find selected food
        food = next((f for f in foods if f["id"] == food_id), None)

        if not food:
            return redirect("/meals")

        food_name = food["name"]

        # Map for piece/serving → grams
        grams_per_piece = {
            "Apple": 150,
            "Banana": 120,
            "Orange": 130,
            "Strawberry": 12,
            "Carrot": 61,
            "Broccoli": 91,
            "Asparagus": 28,
            "Farm Fresh Egg": 50,
            "Milk": 240,
            "Cheese": 28,
            "Chicken": 140,
            "Tofu": 85,
            "Bread": 30,
            "Rice": 158,
            "Oats": 81
        }

        # Convert to grams
        if unit == "grams":
            grams = quantity
        elif unit == "oz":
            grams = quantity * 28.35
        elif unit == "cup":
            grams = quantity * 240
        elif unit in ["piece", "serving"]:
            grams = quantity * grams_per_piece.get(food_name, 100)
        else:
            grams = quantity

        if user:
            meal = {
                "food_id": food_id,
                "name": food_name,
                "quantity": grams,
                "meal_type": meal_type,
                "calories": float(food.get("calories") or 0) * grams / 100,
                "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
                "allergens": food.get("allergens", [])
            }

            user["meals"] = user.get("meals", []) + [meal]
            save_user_data(data)

            return redirect("/meals")

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
    
        # Load saved recipes
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

    return render_template("meals.html", foods=foods, user_meals=user_meals, user_allergies=user_allergies, recipes=recipes, recipe_availability=recipe_availability)


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

@app.post("/log_recipe_meal")
def log_recipe_meal():
    import json
    from datetime import datetime

    recipe_index = int(request.form["recipe_index"])
    meal_type = request.form["meal_type"]

    # Load recipes
    with open("data/saved_recipes.json") as f:
        data = json.load(f)

    recipes = data.get("recipes", [])
    recipe = recipes[recipe_index]

    # 🔥 CHECK INGREDIENTS
    has_all, missing = has_ingredients_for_recipe(recipe)

    if not has_all:
        # Option 1: simple message (quickest)
        return f"Missing ingredients: {', '.join(missing)} <br><a href='/meals'>Go back</a>"

    # ✅ Continue if valid
    meal = {
        "name": recipe["recipe_name"],
        "meal_type": meal_type,
        "calories": 0,
        "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
        "ingredients": recipe["ingredients"]
    }

    # Get user (your existing logic)
    data = load_user_data()
    user_id = session["user"]["id"]
    user = None

    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break

    if user:
        user["meals"] = user.get("meals", []) + [meal]
        save_user_data(data)

    return redirect("/meals")

@app.post("/log_generated_meal")
def log_generated_meal():
    import json
    from datetime import datetime

    recipe = json.loads(request.form["recipe_json"])
    meal_type = request.form["meal_type"]

    meal = {
        "name": recipe["recipe_name"],
        "meal_type": meal_type,
        "calories": 0,
        "timestamp": datetime.now().strftime("%B %d, %Y at %I:%M:%S %p"),
        "ingredients": recipe["ingredients"]
    }

    data = load_user_data()
    user_id = session["user"]["id"]
    user = None
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break
    user["meals"].append(meal)
    save_user_data(data)

    return redirect("/meals")

@app.route("/recipes", methods=["GET", "POST"])
def recipes():
    if not session.get("user"):
        return redirect("/login")

    import json

    FILE_PATH = "data/saved_recipes.json"

    # Load existing recipes
    with open(FILE_PATH, "r") as f:
        data = json.load(f)

    recipes = data.get("recipes", [])

    # 🔹 Handle form submission
    if request.method == "POST":
        new_recipe = {
            "recipe_name": request.form.get("recipe_name"),
            "servings": int(request.form.get("servings", 1)),
            "ingredients": [],
            "steps": [],
            "estimated_time_minutes": 0
        }

        # Handle ingredients (multiple rows)
        names = request.form.getlist("ingredient_name")
        amounts = request.form.getlist("ingredient_amount")
        units = request.form.getlist("ingredient_unit")

        for i in range(len(names)):
            if names[i]:  # skip empty rows
                new_recipe["ingredients"].append({
                    "amount": amounts[i],
                    "unit": units[i],
                    "name": names[i]
                })

        # Optional directions
        steps_text = request.form.get("steps", "").strip()
        if steps_text:
            # Split by lines and remove empty ones
            new_recipe["steps"] = [s.strip() for s in steps_text.splitlines() if s.strip()]

        # Add recipe
        recipes.append(new_recipe)

        # Save back to file
        with open(FILE_PATH, "w") as f:
            json.dump({"recipes": recipes}, f, indent=4)

        return redirect("/recipes")

    return render_template("recipes.html", recipes=recipes)

@app.route("/register")
def register():
    """
    Display the role selection page where user chooses Elderly or Caretaker.
    """
    return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("user"):
        return redirect("/login")

    data = load_user_data()
    user_id = session["user"]["id"]

    # Find the current user
    user = None
    for u in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if u["id"] == user_id:
            user = u
            break

    if not user:
        return "User not found", 404

    # Ensure preferences dict exists
    if "preferences" not in user:
        user["preferences"] = {}
    prefs = user["preferences"]

    # Determine which tab is active
    tab = request.args.get("tab", "interface")

    if request.method == "POST":
        if tab == "interface":
            # Dark mode
            prefs["dark_mode"] = bool(request.form.get("dark_mode"))
            # Language
            prefs["language"] = request.form.get("language", "en")
            # Notifications
            prefs["notifications"] = bool(request.form.get("notifications"))

        elif tab == "privacy":
            # Update password
            new_password = request.form.get("new_password")
            if new_password:
                user["account"]["password"] = bcrypt.generate_password_hash(new_password).decode("utf-8")

        elif tab == "meal":
            # Meal times
            mt = {}
            for meal in ["breakfast", "lunch", "dinner"]:
                hour = int(request.form.get(f"{meal}_hour", 8))
                minute = int(request.form.get(f"{meal}_minute", 0))
                mt[meal] = {"hour": hour, "minute": minute}
            prefs["meal_times"] = mt

            # Preferred cuisines
            cuisines_selected = request.form.getlist("cuisines")
            prefs["preferred_cuisines"] = cuisines_selected

        # Save data back to file
        save_user_data(data)

        # Update session for meal times if elderly
        if user.get("role") == "elderly":
            session["meal_times"] = prefs.get("meal_times", session.get("meal_times"))

        return redirect(url_for("settings") + f"?tab={tab}")

    return render_template("settings.html", preferences=prefs, active_tab=tab)

@app.post("/recipes/<int:recipe_index>/delete")
def delete_recipe(recipe_index):
    from pathlib import Path
    import json

    file_path = Path("data/saved_recipes.json")

    # Load correctly
    if file_path.exists() and file_path.stat().st_size > 0:
        data = json.loads(file_path.read_text())
    else:
        data = {"recipes": []}

    recipes = data.get("recipes", [])

    # Validate index
    if 0 <= recipe_index < len(recipes):
        removed = recipes.pop(recipe_index)
        print(f"Deleted recipe: {removed['recipe_name']}")

        # Save back in SAME STRUCTURE
        file_path.write_text(json.dumps({"recipes": recipes}, indent=4))

    return redirect(url_for("recipes"))
# ------------------ Run App ------------------
if __name__ == "__main__":
    app.run(debug=True)
