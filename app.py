import os

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify
from sqlalchemy import text
from config import Config
from extensions import db
from auth.models import User
from auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY",
        app.config["SECRET_KEY"]
    )
    db.init_app(app)
    app.register_blueprint(auth_bp)

    # Import models before create_all so SQLAlchemy registers every table.
    from billing import models  # noqa: F401
    from billing import init_billing
    init_billing(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return jsonify({"message": "Brightloop Billing API is running!"})

    @app.route("/api/db-check")
    def database_check():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return jsonify({"status": "success",
                            "message": "MySQL connected successfully!"})
        except Exception as error:
            return jsonify({"status": "error", "message": str(error)}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
