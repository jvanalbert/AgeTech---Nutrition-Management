import json
import os
from dotenv import load_dotenv
from Backend.food_safety import check_food_safety

# ----- Load sample food and user data ----- #

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_food():
    with open(os.path.join(DATA_DIR, "sample_food.json"), "r") as file:
        return json.load(file)
#Load a single elderly user's data from sample_user.json. Defaults to user_id=1  
def load_user(user_id=1):
    with open(os.path.join(DATA_DIR, "sample_user.json"), "r") as file:
        data = json.load(file)
    
    elderly_users = data.get("elderly_users", [])
    # Find the user with the specified ID
    user = next((u for u in elderly_users if u["id"] == user_id), {})
    
    return user

#Get list of foods to not include in recipes
def get_restricted_foods():
    # Load the JSON with all items
    data = load_food()
    # Extract just the food names
    food_names = [item["product"]["name"] for item in data.get("items", [])]
    
    # Run your existing check_food_safety function
    _, unsafe_foods = check_food_safety(food_names)
    
    return unsafe_foods

restricted = get_restricted_foods()
print("Foods to avoid:", restricted)

#Get available household ingredients
def get_available_ingredients():
    data = load_food()
    items = data.get("items", [])
    return [item["product"]["name"] for item in items]

# ----- AI Recipe Generation ----- #

#Recipe prompt for OpenAI
def build_recipe_prompt(meal_type="dinner"):

    user = load_user()
    ingredients = get_available_ingredients()
    restricted = get_restricted_foods()

    dietary_restrictions = user.get("dietary_restrictions", [])
    preferred_cuisines = user.get("preferred_cuisines", [])
    cooking_skill = user.get("cooking_skill", 1)

    # Skill level instructions
    skill_rules = {
        1: "Very beginner: Use simple cooking techniques. Maximum 6 steps.",
        2: "Beginner: Keep the recipe simple. Maximum 6 steps.",
        3: "Intermediate: Moderate complexity allowed. Maximum 8 steps.",
        4: "Advanced: Normal recipe complexity allowed.",
        5: "Expert: Normal recipe complexity allowed."
    }

    skill_instruction = skill_rules.get(cooking_skill, skill_rules[1])

    prompt = f"""
        You are a recipe generator.

        Generate a recipe using ONLY the provided ingredients.

        Available ingredients:
        {ingredients}

        Constraints:
        - Avoid restricted foods: {restricted}
        - Consider dietary restrictions: {dietary_restrictions}
        - Consider preferred cuisines: {preferred_cuisines}
        - Meal type: {meal_type}
        - Skill level: {skill_instruction}

        Ingredient Rules:
        - Ingredient names must be simple food names (e.g., "chicken breast", "white rice", "broccoli").
        - Do NOT include preparation words like "chopped" or "diced".

        Return ONLY valid JSON in this format:

        {{
        "recipe_name": "",
        "servings": 1,
        "ingredients": [
            {{ "amount": "", "unit": "", "name": "" }}
        ],
        "steps": [],
        "estimated_time_minutes": 0
        }}
        """
    return prompt

#Calling OpenAi to generate recipe
from openai import AzureOpenAI
load_dotenv()  # Load environment variables from .env file
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
key = os.getenv("AZURE_OPENAI_KEY1")

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint = endpoint,
    api_key = key,
)

def generate_recipe(meal_type="dinner"):
    # 1️⃣ Build the prompt
    prompt = build_recipe_prompt(meal_type)

    # 2️⃣ Call Azure OpenAI
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # deployment name from .env
        messages=[
            {"role": "system", "content": "You generate structured cooking recipes."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    # 3️⃣ RETURN the AI response (important!)
    return response.choices[0].message.content

#save recipe function to saved recipe files (if user liked, will ask after meal)

#get nutritional information from recipe 

#testing prompt 
if __name__ == "__main__":
    print("=== TEST: Generate breakfast recipe ===\n")

    # Call the function
    recipe_json = generate_recipe("breakfast")  # "breakfast" meal type

    try:
        # Parse the response JSON
        recipe = json.loads(recipe_json)
        print("Recipe Name:", recipe.get("recipe_name"))
        print("Servings:", recipe.get("servings"))
        print("Estimated time (minutes):", recipe.get("estimated_time_minutes"))
        print("\nIngredients:")
        for ing in recipe.get("ingredients", []):
            print(f"- {ing['amount']} {ing['unit']} {ing['name']}")
        print("\nSteps:")
        for i, step in enumerate(recipe.get("steps", []), 1):
            print(f"{i}. {step}")

    except json.JSONDecodeError:
        print("Error: Could not parse recipe JSON from model output:")
        print(recipe_json)