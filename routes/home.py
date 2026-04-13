from flask import Blueprint, render_template, session, redirect
from Backend.user_loader import load_user_data
from services.nutrition_service import *

home_bp = Blueprint("home", __name__)

@home_bp.route("/home")
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