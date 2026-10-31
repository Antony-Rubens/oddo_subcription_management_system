from flask import Flask
from config import Config
from extensions import db
from sqlalchemy import text

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


@app.route("/")
def home():
    return "Subscription Management System is running!"


@app.route("/test-db")
def test_db():
    try:
        db.session.execute(text("SELECT 1"))
        return {
            "status": "success",
            "message": "Flask connected to MySQL successfully!"
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500


if __name__ == "__main__":
    app.run(debug=True)