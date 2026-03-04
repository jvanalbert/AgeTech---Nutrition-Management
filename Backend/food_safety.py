import json
import os

# ----- Load data ----- #

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_users():
    with open(os.path.join(DATA_DIR, "sample_user.json"), "r") as file:
        return json.load(file)

def load_med_conflicts():
    with open(os.path.join(DATA_DIR, "med_food_conflicts.json"), "r") as file:
        return json.load(file)

# ----- Main Safety Check Function ----- #
# Returns a warning if any conflicts are found and list of those conflicting foods.
def check_food_safety(user_foods):
    users_data = load_users()
    med_conflicts = load_med_conflicts()

    elderly_users = users_data["elderly_users"]
    user = next(user for user in elderly_users if user["id"] == 1)

    user_meds = user.get("medications", [])
    user_allergies = user.get("allergies", [])

    warnings = []
    unsafe_foods = set()  # <- this is new

    # ----- Medication Checks ----- #
    for med in user_meds:
        if med in med_conflicts:
            med_data = med_conflicts[med]
            avoid_list = med_data.get("avoid", [])
            reason = med_data.get("reason", "No reason provided.")
            severity = med_data.get("severity", "unknown")

            for food in user_foods:
                if food.lower() in avoid_list:
                    unsafe_foods.add(food.lower())

                    message = (
                        f"⚠️ WARNING ({severity.upper()}): "
                        f"{food.title()} should be avoided while taking {med}.\n"
                        f"Reason: {reason}.\n"
                        f"Please consult your doctor or pharmacist before making dietary changes."
                    )

                    warnings.append(message)

    # ----- Allergy Checks ----- #
    for food in user_foods:
        if food.lower() in user_allergies:
            unsafe_foods.add(food.lower())

            message = (
                f"🚨 ALLERGY ALERT: {food.title()} is listed as an allergy.\n"
                f"This food should be avoided completely."
            )

            warnings.append(message)

    return warnings, list(unsafe_foods)

# ----- Terminal Test ----- #
if __name__ == "__main__":
    test_foods = ["spinach", "chicken", "peanuts"]

    warnings, unsafe = check_food_safety(test_foods)

    print("UNSAFE FOODS:", unsafe)
    print()

    for w in warnings:
        print(w)
        print()