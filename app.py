
from flask import Flask, jsonify
from sqlalchemy import text

from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database
    db.init_app(app)

    # Import models so SQLAlchemy registers their tables
    from billing import models as billing_models
    from subscription_product import models as product_models

    # Register billing blueprint
    from billing import init_billing
    init_billing(app)

    # Register product blueprint
    from subscription_product import product_bp
    app.register_blueprint(product_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return jsonify({
            "message": "Subscription Management System is running!"
        })

    @app.route("/test-db")
    def test_db():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify({
                "status": "success",
                "message": "Flask connected to MySQL successfully!"
            }), 200
        except Exception as error:
            return jsonify({
                "status": "error",
                "message": str(error)
            }), 500

    @app.route("/api/db-check")
    def database_check():
        try:
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            return jsonify({
                "status": "success",
                "message": "MySQL connected successfully!"
            }), 200
        except Exception as error:
            return jsonify({
                "status": "error",
                "message": str(error)
            }), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
