from flask import Flask
from app.routes import bp

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = "dev"  # Use a secure, random key in production
    app.register_blueprint(bp)
    return app