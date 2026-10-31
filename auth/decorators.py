from functools import wraps
from flask import request, jsonify, current_app, g
import jwt

from extensions import db
from auth.models import User, RevokedToken


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({"message": "Token required"}), 401

        token = header.split(" ", 1)[1]

        try:
            secret = current_app.config.get("JWT_SECRET_KEY") or current_app.config["SECRET_KEY"]

            data = jwt.decode(token, secret, algorithms=["HS256"])

            jti = data.get("jti")

            if not jti or db.session.get(RevokedToken, jti):
                return jsonify({"message": "Token has been revoked or is invalid"}), 401

            user = db.session.get(User, data["user_id"])

            if not user or not user.is_active:
                return jsonify({"message": "User not found or inactive"}), 401

            g.current_user = user

        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):

            if g.current_user.role not in roles:
                return jsonify({"message": "Access denied"}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator