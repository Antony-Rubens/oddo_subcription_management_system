import os
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv(override=True)

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False