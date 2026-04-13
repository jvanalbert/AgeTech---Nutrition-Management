from flask import Blueprint, render_template, request, redirect, session
from services.auth_service import check_login

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def root():
    if session.get("user"):
        return redirect("/home")
    return redirect("/login")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = check_login(request.form["username"], request.form["password"])

        if user:
            session["user"] = {
                "id": user["id"],
                "role": user.get("role"),
                "name": user.get("name")
            }
            return redirect("/home")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")