from flask import request, jsonify
from . import auth_bp
from .services import register_user
from auth.services import login_user

from flask import g
from auth.decorators import token_required, role_required
from auth.models import User
from extensions import db


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_profile():
    user = g.current_user

    return jsonify({
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }), 200


@auth_bp.route("/users", methods=["GET"])
@role_required("Admin")
def get_users():
    users = User.query.all()

    return jsonify([
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active
        }
        for u in users
    ]), 200


@auth_bp.route("/users/<int:user_id>/status", methods=["PATCH"])
@role_required("Admin")
def update_user_status(user_id):
    user = db.session.get(User, user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json(silent=True) or {}

    if not isinstance(data.get("is_active"), bool):
        return jsonify({"message": "is_active must be true or false"}), 400

    user.is_active = data["is_active"]
    db.session.commit()

    return jsonify({"message": "User status updated"}), 200


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")

    try:
        user = register_user(
            full_name,
            email,
            password
        )

        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role
            }
        }), 201

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 400

    except Exception:
        return jsonify({
            "success": False,
            "message": "Something went wrong"
        }), 500


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    try:
        user, token = login_user(
            data.get("email"),
            data.get("password")
        )

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role
            }
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 401

    except Exception:
        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500
