from flask import Blueprint, render_template, session, redirect
from Backend.user_loader import load_user_data
from services.nutrition_service import (
    track_calories,
    track_protein,
    track_cholesterol,
    track_sugar,
    track_sodium
)
from datetime import datetime

nutrition_bp = Blueprint("nutrition", __name__)


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


@nutrition_bp.route("/nutrition")
def nutrition():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    # 🔥 FIX: use target user
    user = get_target_user(data, session_user)

    if not user:
        return redirect("/home")

    # --- Nutrition calculations ---
    calories = track_calories(user)
    protein = track_protein(user)
    cholesterol = track_cholesterol(user)
    sugar = track_sugar(user)
    sodium = track_sodium(user)

    return render_template(
        "nutrition.html",
        user=user,
        viewer=session_user,   # 👈 important for UI control
        current_date=datetime.now().strftime("%B %d, %Y"),

        # Calories
        **calories,

        # Protein
        protein_goal=protein.get("goal", 0),
        protein_consumed=protein.get("consumed", 0),
        protein_remaining=protein.get("remaining", 0),

        # Cholesterol
        cholesterol_goal=cholesterol.get("goal", 0),
        cholesterol_consumed=cholesterol.get("consumed", 0),
        cholesterol_remaining=cholesterol.get("remaining", 0),

        # Sugar
        sugar_goal=sugar.get("goal", 0),
        sugar_consumed=sugar.get("consumed", 0),
        sugar_remaining=sugar.get("remaining", 0),

        # Sodium
        sodium_goal=sodium.get("goal", 0),
        sodium_consumed=sodium.get("consumed", 0),
        sodium_remaining=sodium.get("remaining", 0),
    )

@nutrition_bp.route("/nutrition/history")
def nutrition_history():
    if not session.get("user"):
        return redirect("/login")

    data = load_user_data()
    session_user = session["user"]
    user = get_target_user(data, session_user)
    meals = user.get('meals', [])

    # Nested dictionary: Month -> Day -> Totals/Meals
    grouped_history = {}

    for meal in meals:
        if "timestamp" in meal:
            # Example timestamp: "April 20, 2026 at 05:10:38 PM"
            parts = meal["timestamp"].split(" ")
            
            # parts[0] is Month, parts[1] is Day, parts[2] is Year
            month_year = f"{parts[0]} {parts[2]}" 
            full_date = f"{parts[0]} {parts[1]} {parts[2]}"

            # Ensure the Month exists
            if month_year not in grouped_history:
                grouped_history[month_year] = {}
            
            # Ensure the Day exists and initialize all 5 tracking keys
            if full_date not in grouped_history[month_year]:
                grouped_history[month_year][full_date] = {
                    "meals": [],
                    "total_cal": 0.0,
                    "total_prot": 0.0,
                    "total_chol": 0.0,
                    "total_sug": 0.0,
                    "total_sod": 0.0
                }
            
            day_data = grouped_history[month_year][full_date]
            
            # Append the meal to the list
            day_data["meals"].append(meal)
            
            # Aggregate all nutrient totals (using .get with a default of 0 for safety)
            day_data["total_cal"] += float(meal.get("calories", 0))
            day_data["total_prot"] += float(meal.get("protein", 0))
            day_data["total_chol"] += float(meal.get("cholesterol", 0))
            day_data["total_sug"] += float(meal.get("sugar", 0))
            day_data["total_sod"] += float(meal.get("sodium", 0))

    return render_template(
        "history.html", 
        grouped_history=grouped_history, 
        viewer=session_user,
        user=user
    )