from flask import Blueprint, render_template, session, redirect, request, url_for
from Backend.user_loader import load_user_data, save_user_data
from extensions import bcrypt

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("user"):
        return redirect("/login")

    data = load_user_data()
    user_id = session["user"]["id"]

    user = next((u for u in data["elderly_users"] if u["id"] == user_id), None)

    if not user:
        return "User not found", 404

    prefs = user.setdefault("preferences", {})
    tab = request.args.get("tab", "interface")

    if request.method == "POST":
        if tab == "privacy":
            new_password = request.form.get("new_password")
            if new_password:
                user["account"]["password"] = bcrypt.generate_password_hash(new_password).decode("utf-8")

        save_user_data(data)
        return redirect(url_for("settings.settings", tab=tab))

    return render_template("settings.html", preferences=prefs, active_tab=tab)