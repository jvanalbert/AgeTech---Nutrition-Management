from Backend.user_loader import load_user_data
from extensions import bcrypt

def check_login(username, password):
    data = load_user_data()

    for user in data.get("elderly_users", []) + data.get("caretaker_users", []):
        if user["account"]["username"] == username:
            if bcrypt.check_password_hash(user["account"]["password"], password):
                return user

    return None