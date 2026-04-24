from flask import Blueprint, render_template, session, redirect, request
from Backend.user_loader import load_user_data, save_user_data, load_elderly_users_with_caretakers

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile")
def profile():
    if not session.get("user"):
        return redirect("/login")

    data = load_user_data()
    users = load_elderly_users_with_caretakers()

    return render_template(
        "profile.html",
        users=users,
        viewer=session.get("user", {})
    )

# @profile_bp.route("/edit_meal_times/<int:user_id>", methods=["GET", "POST"])
# def edit_meal_times(user_id):
#     if not session.get("user"):
#         return redirect("/login")

#     data = load_user_data()

#     # Find user
#     user = next(
#         (u for u in data.get("elderly_users", []) if u["id"] == user_id),
#         None
#     )

#     if not user:
#         return "User not found", 404

#     # Default structure (VERY IMPORTANT for avoiding Jinja crashes)
#     default_meal_times = {
#         "breakfast": {"hour": 8, "minute": 0},
#         "lunch": {"hour": 12, "minute": 0},
#         "dinner": {"hour": 18, "minute": 0}
#     }

#     # Ensure meal_times ALWAYS exists
#     if "meal_times" not in user or not user["meal_times"]:
#         user["meal_times"] = default_meal_times

#     meal_times = user["meal_times"]

#     # ---------------- POST (save updates) ----------------
#     if request.method == "POST":
#         user["meal_times"] = {
#             "breakfast": {
#                 "hour": int(request.form.get("breakfast_hour", 8)),
#                 "minute": int(request.form.get("breakfast_minute", 0))
#             },
#             "lunch": {
#                 "hour": int(request.form.get("lunch_hour", 12)),
#                 "minute": int(request.form.get("lunch_minute", 0))
#             },
#             "dinner": {
#                 "hour": int(request.form.get("dinner_hour", 18)),
#                 "minute": int(request.form.get("dinner_minute", 0))
#             }
#         }

#         save_user_data(data)

#         # If user is editing their own account, keep session in sync
#         if session["user"]["id"] == user_id:
#             session["meal_times"] = user["meal_times"]

#         return redirect("/profile")

#     # ---------------- GET (render page) ----------------
#     return render_template(
#         "edit_meal_times.html",
#         user=user,
#         meal_times=meal_times
#     )