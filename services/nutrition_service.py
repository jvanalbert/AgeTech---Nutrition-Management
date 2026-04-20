from datetime import datetime

# Helper to get today's date string once
def get_today():
    return datetime.now().strftime("%Y-%m-%d")

# tracks calories based on a 2000 calorie diet
def track_calories(user):
    goal = user.get("daily_calories", 2000)
    meals = user.get("meals", [])
    today = get_today()

    consumed = sum(meal.get("calories", 0) for meal in meals if meal.get("date") == today)
    remaining = goal - consumed

    return {"goal": goal, "consumed": consumed, "remaining": remaining}

# determines protein by body weight (lbs x 1.2)
def get_protein_goal(user):
    weight = user.get("weight_lbs", 0)
    protein_goal = weight * 1.2
    return round(protein_goal, 1)

def track_protein(user):
    goal = get_protein_goal(user)
    meals = user.get("meals", [])
    today = get_today()

    consumed = sum(meal.get("protein", 0) for meal in meals if meal.get("date") == today)
    remaining = goal - consumed

    return {"goal": goal, "consumed": consumed, "remaining": remaining}

# cholestrol for user
def get_cholesterol_goal(user):
    medications = user.get("medications", [])
    medications_lower = [med.lower() for med in medications]
    stricter_goal_meds = ["statins", "atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "lovastatin", "fluvastatin", "pitavastatin"]

    if any(med in medications_lower for med in stricter_goal_meds):
        return 200
    return 300

def track_cholesterol(user):
    goal = get_cholesterol_goal(user)
    meals = user.get("meals", [])
    today = get_today()

    consumed = sum(meal.get("cholesterol", 0) for meal in meals if meal.get("date") == today)
    remaining = goal - consumed

    return {"goal": goal, "consumed": consumed, "remaining": remaining}

# if male -> 36 g, female -> 25 g
def get_sugar_goal(user):
    gender = user.get("gender", "").lower()
    return 36 if gender == "male" else 25

def track_sugar(user):
    goal = get_sugar_goal(user)
    meals = user.get("meals", [])
    today = get_today()

    consumed = sum(meal.get("sugar", 0) for meal in meals if meal.get("date") == today)
    remaining = goal - consumed

    return {"goal": goal, "consumed": consumed, "remaining": remaining}

# 1300 mg for any person over 50
def get_sodium_goal(user):
    return 1300

def track_sodium(user):
    goal = get_sodium_goal(user)
    meals = user.get("meals", [])
    today = get_today()

    consumed = sum(meal.get("sodium", 0) for meal in meals if meal.get("date") == today)
    remaining = goal - consumed

    return {"goal": goal, "consumed": consumed, "remaining": remaining}