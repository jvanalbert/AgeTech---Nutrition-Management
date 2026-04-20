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