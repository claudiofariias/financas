from flask import Flask
from app.routes import bp

def format_currency(value):
    return f"R${value:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )

    app.secret_key = "dev"
    app.register_blueprint(bp)

    app.jinja_env.filters['currency'] = format_currency

    return app