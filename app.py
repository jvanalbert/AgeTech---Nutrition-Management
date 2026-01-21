from flask import Flask, render_template
from food_loader import load_foods
from user_loader import load_users

app = Flask(__name__)

foods = load_foods("data/sample_foods.xml")
users = load_users("data/sample_user.xml")

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/users")
def profile():
    return render_template("users.html", users=users)

@app.route("/foods")
def food_list():
    return render_template("foods.html", foods=foods)

if __name__ == "__main__":
    app.run(debug=True)
