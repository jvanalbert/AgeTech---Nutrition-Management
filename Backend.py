# Backend functions 
from user_loader import load_users
from food_loader import load_foods
import random

# dietary restrictions to food preferences
DIETARY_FOOD_PREFERENCES = {
    "low sodium": ["fruit", "vegetable"],
    "low salt": ["fruit", "vegetable"],
    "heart healthy": ["fruit", "vegetable", "grain"],
    "diabetic": ["vegetable", "grain"],
    "diabetes": ["vegetable", "grain"],
    "cholesterol": ["fruit", "vegetable", "grain"],
    "high cholesterol": ["fruit", "vegetable", "grain"]
}

def get_user_profiles():
    """Get all available user profiles from XML"""
    try:
        users = load_users("data/sample_user.xml")
        return [{
            "id": user["id"],
            "name": user["name"],
            "age": user["age"],
            "dietary_restrictions": user["dietary_restrictions"],
            "allergies": user["allergies"],
            "daily_calories": user["daily_calories"],
            "cooking_skill": user["cooking_skill"],
            "preferred_cuisines": user["preferred_cuisines"]
        } for user in users]
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

def get_user_profile(user_id):
    """Get a specific user profile by ID"""
    profiles = get_user_profiles()
    return next((profile for profile in profiles if profile["id"] == user_id), None)

def get_meal_recommendations(user_id, meal_time):
    """Get 3 meal recommendations for a user at a specific meal time"""
    user = get_user_profile(user_id)
    foods = load_foods("data/sample_foods.xml")

    if not user or not foods:
        return []

    meals = []
    for i in range(3):
        meal = generate_meal(user, foods, meal_time)
        if meal:
            meals.append(meal)

    return meals

def generate_meal(user, foods, meal_time):
    """Generate a simple meal for the user from safe foods""" 
    safe_foods = [food for food in foods if not any(allergy.lower() in food["name"].lower() for allergy in user["allergies"])]

    if len(safe_foods) < 2:
        return None

    # 2-3 random foods
    num_foods = min(random.randint(2, 3), len(safe_foods))
    selected_foods = random.sample(safe_foods, num_foods)

    
    total_calories = sum(food["calories"] for food in selected_foods)

    # meal name
    food_names = [food["name"] for food in selected_foods]
    meal_name = f"{meal_time.title()}: {', '.join(food_names)}"

    return {
        "id": random.randint(1000, 9999),
        "name": meal_name,
        "description": f"A simple {meal_time.lower()} meal",
        "foods": [{"name": food["name"], "category": food["category"]} for food in selected_foods],
        "total_calories": total_calories,
        "categories": list(set(food["category"] for food in selected_foods))
    }

def get_meal_times():
    """Get available meal times"""
    return ["breakfast", "lunch", "dinner"] 