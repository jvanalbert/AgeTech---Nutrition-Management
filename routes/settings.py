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

        # 🔒 Only allow elderly to change password
        if tab == "privacy" and session_user.get("role") == "elderly":
            new_password = request.form.get("new_password")

            if new_password:
                user["account"]["password"] = (
                    bcrypt.generate_password_hash(new_password).decode("utf-8")
                )

        save_user_data(data)
        return redirect(url_for("settings.settings", tab=tab))

    return render_template(
        "settings.html",
        preferences=prefs,
        active_tab=tab,
        user=user,              # 👈 important
        viewer=session_user     # 👈 fixes Jinja error
    )