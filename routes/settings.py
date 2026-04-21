from flask import Blueprint, render_template, session, redirect, request, url_for
from Backend.user_loader import load_user_data, save_user_data
from extensions import bcrypt

settings_bp = Blueprint("settings", __name__)


def get_target_user(data, session_user):
    role = session_user.get("role", "").lower()

    if role == "caretaker":
        return next(
            (u for u in data.get("elderly_users", [])
             if u.get("caretaker_id") == session_user["id"]),
            None
        )

    elif role == "elderly":
        return next(
            (u for u in data.get("elderly_users", [])
             if u["id"] == session_user["id"]),
            None
        )

    return None


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("user"):
        return redirect("/login")

    session_user = session["user"]
    data = load_user_data()

    user = get_target_user(data, session_user)

    if not user:
        return redirect("/home")

    prefs = user.setdefault("preferences", {})
    tab = request.args.get("tab", "interface")

    # =====================
    # POST updates
    # =====================
    if request.method == "POST":

    # ---------------------
    # Interface Settings
    # ---------------------
        if tab == "interface":
            prefs["language"] = request.form.get("language", "en")
            prefs["dark_mode"] = request.form.get("dark_mode") == "1"
            prefs["notifications"] = request.form.get("notifications") == "1"

        # ---------------------
        # Privacy (Password)
        # ---------------------
        elif tab == "privacy" and session_user.get("role") == "elderly":
            new_password = request.form.get("new_password")

            if new_password:
                user["account"]["password"] = (
                    bcrypt.generate_password_hash(new_password).decode("utf-8")
                )

        # ---------------------
        # Meal Preferences
        # ---------------------
        elif tab == "meal":

            # Meal Times
            meal_times = {}
            for meal in ["breakfast", "lunch", "dinner"]:
                hour = int(request.form.get(f"{meal}_hour", 0))
                minute = int(request.form.get(f"{meal}_minute", 0))

                meal_times[meal] = {
                    "hour": hour,
                    "minute": minute
                }

            prefs["meal_times"] = meal_times

            # Preferred Cuisines (checkbox list)
            prefs["preferred_cuisines"] = request.form.getlist("cuisines")

        # SAVE EVERYTHING
        save_user_data(data)

        return redirect(url_for("settings.settings", tab=tab))

    return render_template(
        "settings.html",
        preferences=prefs,
        active_tab=tab,
        user=user,              # 👈 important
        viewer=session_user     # 👈 fixes Jinja error
    )