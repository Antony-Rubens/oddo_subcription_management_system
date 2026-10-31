from werkzeug.security import check_password_hash
from flask import current_app
import jwt
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from extensions import db
from auth.models import User


def register_user(full_name, email, password):

    # Validate input
    if not full_name or not email or not password:
        raise ValueError("All fields are required")

    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) > 100:
        raise ValueError("Name must be under 100 characters")

    if len(email) > 120 or "@" not in email:
        raise ValueError("Please enter a valid email address")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        raise ValueError("Email is already registered")

    # Hash the password
    password_hash = generate_password_hash(password)

    # Create user
    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role="Customer"
    )

    try:
        db.session.add(new_user)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        raise ValueError("Email is already registered")

    except Exception:
        db.session.rollback()
        raise

    return new_user



def login_user(email, password):

    if not email or not password:
        raise ValueError("Email and password are required")

    user = User.query.filter_by(email=email.strip().lower()).first()

    if not user or not check_password_hash(user.password_hash, password):
        raise ValueError("Invalid email or password")

    if not user.is_active:
        raise ValueError("Account is inactive")

    secret = current_app.config.get("JWT_SECRET_KEY") or current_app.config["SECRET_KEY"]

    token = jwt.encode({
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }, secret, algorithm="HS256")

    return user, token

