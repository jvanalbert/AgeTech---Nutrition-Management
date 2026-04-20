from flask import Blueprint, render_template, session, redirect
from Backend.user_loader import load_user_data
from services.nutrition_service import *

home_bp = Blueprint("home", __name__)

@home_bp.route("/home")
def home():
    if not session.get("user"):
        return redirect("/login")
    
    user = session["user"]

    data = load_user_data()
    target_user = None

    # If caretaker → find their elderly user
    if user.get("role") == "caretaker":
      if user.get("role") == "caretaker":
        for u in data.get("elderly_users", []):
            if u.get("caretaker_id") == user["id"]:
                target_user = u
                break

    # If elderly → they are the target
    elif user.get("role") == "elderly":
        for u in data.get("elderly_users", []):
            if u["id"] == user["id"]:
                target_user = u
                break

    nutrition_data = None

    if target_user:
        calorie_totals = track_calories(target_user)
        protein_totals = track_protein(target_user)
        cholesterol_totals = track_cholesterol(target_user)
        sugar_totals = track_sugar(target_user)
        sodium_totals = track_sodium(target_user)

        nutrition_data = {
            "calories": calorie_totals,
            "protein": protein_totals,
            "cholesterol": cholesterol_totals,
            "sugar": sugar_totals,
            "sodium": sodium_totals
        }
    
    # Get nutrition data if user is elderly
    # nutrition_data = None
    # if user.get("role") == "elderly":
    #     data = load_user_data()
    #     elderly_user = None
    #     for u in data.get("elderly_users", []):
    #         if u["id"] == user["id"]:
    #             elderly_user = u
    #             break
        
    #     if elderly_user:
    #         calorie_totals = track_calories(elderly_user)
    #         protein_totals = track_protein(elderly_user)
    #         cholesterol_totals = track_cholesterol(elderly_user)
    #         sugar_totals = track_sugar(elderly_user)
    #         sodium_totals = track_sodium(elderly_user)
            
    #         nutrition_data = {
    #             "calories": calorie_totals,
    #             "protein": protein_totals,
    #             "cholesterol": cholesterol_totals,
    #             "sugar": sugar_totals,
    #             "sodium": sodium_totals
    #         }
    
    return render_template("home.html", user=target_user, viewer=user, nutrition=nutrition_data)