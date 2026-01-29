from flask import Flask
from flask_bcrypt import Bcrypt
from Backend.user_loader import load_user_data, save_user_data

app = Flask(__name__)
bcrypt = Bcrypt(app)

def hash_password():
    data = load_user_data()
    for user in data.get("elderly_users", []) + data.get("caretaker_users", []):
        password = user["account"]["password"]
        if not password.startswith("$2b$"):  # Check if already hashed, bcrypt hashes alwasy start with $2b$
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user["account"]["password"] = hashed
        save_user_data(data)
        print("Passwords hashed successfully.") #will print twice, once for elderly and once for caretaker

if __name__ == "__main__":
    hash_password()