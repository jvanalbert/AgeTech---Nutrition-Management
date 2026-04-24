from flask import Flask, session
from Backend.user_loader import load_user_data
from utils.helpers import get_target_user
from extensions import bcrypt

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"

    bcrypt.init_app(app)

    @app.context_processor
    def inject_user_data():
        from Backend.user_loader import load_user_data

        user = session.get("user")

        if user:
            data = load_user_data()
            u = get_target_user(data, user)

            return {
                "preferences": u.get("preferences", {}) if u else {},
                "viewer": user
            }

        return {
            "preferences": {},
            "viewer": None
        }
    
    @app.context_processor
    def inject_meal_times():
        if not session.get("user"):
            return {}

        data = load_user_data()
        session_user = session.get("user")

        # reuse your helper
        user = get_target_user(data, session_user)

        if not user:
            return {}

        meal_times = user.get("preferences", {}).get("meal_times", {})

        return dict(meal_times=meal_times)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.home import home_bp
    from routes.meals import meals_bp
    from routes.foods import foods_bp
    from routes.recipes import recipes_bp
    from routes.nutrition import nutrition_bp
    from routes.profile import profile_bp
    from routes.settings import settings_bp
    from routes.register import register_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(meals_bp)
    app.register_blueprint(foods_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(register_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)