# Backend functions 
from Backend.user_loader import load_users
from Backend.food_loader import load_foods
import random

# dietary restrictions to food preferences
DIETARY_FOOD_PREFERENCES = {
    "low sodium": ["fruit", "vegetable", "protein"], #restriction
    "gluten free": ["fruit", "vegetable", "protein"], #restriction
    "heart healthy": ["fruit", "vegetable", "grain", "protein", "dairy"], #preference
    "diabetic": ["vegetable", "grain", "protein"], #restriction
    "high cholesterol": ["fruit", "vegetable", "grain"], #restriction
    "vegetarian": ["fruit", "vegetable", "grain", "dairy"], #preference
    "lactose intolerant": ["fruit", "vegetable", "grain", "protein"] #restriction
}

def get_user_profiles():
    """Get all available user profiles from JSON"""
    try:
        users = load_users("data/users.json")
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

