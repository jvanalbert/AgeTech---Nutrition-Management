from flask import Blueprint, render_template, session, redirect, request, url_for
from Backend.user_loader import load_user_data, save_user_data
from utils.helpers import get_target_user
from extensions import bcrypt

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not session.get("user"):
        return redirect("/login")

    session_user = session.get("user", {})
    data = load_user_data()

    user = get_target_user(data, session_user)

    if not user:
        return redirect("/home")

    prefs = user.setdefault("preferences", {})
    meal_times = prefs.setdefault("meal_times", {
        "breakfast": {"hour": 8, "minute": 0},
        "lunch": {"hour": 12, "minute": 0},
        "dinner": {"hour": 18, "minute": 0}
    })

    tab = request.args.get("tab", "meal")

    if request.method == "POST":

        # ---------------------
        # Privacy
        # ---------------------
        if tab == "privacy" and session_user.get("role") == "elderly":
            new_password = request.form.get("new_password")

            if new_password:
                user["account"]["password"] = (
                    bcrypt.generate_password_hash(new_password).decode("utf-8")
                )

        # ---------------------
        # Meal + Health + Interface
        # ---------------------
        elif tab == "meal":

            # Meal times
            meal_times = {}
            for meal in ["breakfast", "lunch", "dinner"]:
                meal_times[meal] = {
                    "hour": int(request.form.get(f"{meal}_hour") or 0),
                    "minute": int(request.form.get(f"{meal}_minute") or 0)
                }

            prefs["meal_times"] = meal_times

            # Cuisines
            prefs["preferred_cuisines"] = request.form.getlist("cuisines")

            # Dietary restrictions
            prefs["dietary_restrictions"] = request.form.get("dietary_restrictions", "")

            # ✅ DARK MODE (moved here for simplicity)
            prefs["dark_mode"] = "dark_mode" in request.form

        save_user_data(data)
        return redirect(url_for("settings.settings", tab=tab))

    return render_template(
        "settings.html",
        preferences=prefs or {},
        meal_times=meal_times,
        active_tab=tab,
        user=user,
        viewer=session_user
    )