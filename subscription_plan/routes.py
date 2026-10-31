
from decimal import Decimal, InvalidOperation

from flask import request, jsonify

from extensions import db
from subscription_plan import plan_bp
from subscription_plan.models import SubscriptionPlan
from subscription_product.models import ProductVariant


ALLOWED_INTERVALS = [
    "monthly",
    "quarterly",
    "half_yearly",
    "yearly"
]


def serialize_plan(plan):
    return {
        "id": plan.id,
        "variant_id": plan.variant_id,
        "plan_name": plan.plan_name,
        "billing_interval": plan.billing_interval,
        "price": float(plan.price),
        "trial_days": plan.trial_days,
        "description": plan.description,
        "is_active": plan.is_active,
        "created_at": plan.created_at.isoformat()
        if plan.created_at else None
    }


def validate_price(value):
    try:
        price = Decimal(str(value))
        if not price.is_finite() or price <= 0:
            return None
        return price
    except (InvalidOperation, TypeError, ValueError):
        return None


# CREATE SUBSCRIPTION PLAN
@plan_bp.route("/", methods=["POST"])
def create_plan():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "variant_id",
        "plan_name",
        "billing_interval",
        "price"
    ]

    for field in required_fields:
        if field not in data or data[field] in (None, ""):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    variant = db.session.get(ProductVariant, data["variant_id"])

    if not variant:
        return jsonify({
            "error": "Product variant not found"
        }), 404

    if not variant.is_active:
        return jsonify({
            "error": "Cannot create a plan for an inactive variant"
        }), 400

    interval = data["billing_interval"]

    if interval not in ALLOWED_INTERVALS:
        return jsonify({
            "error": "Invalid billing interval",
            "allowed_values": ALLOWED_INTERVALS
        }), 400

    price = validate_price(data["price"])

    if price is None:
        return jsonify({
            "error": "Price must be a positive number"
        }), 400

    try:
        trial_days = int(data.get("trial_days", 0))
    except (ValueError, TypeError):
        return jsonify({
            "error": "trial_days must be a non-negative integer"
        }), 400

    if trial_days < 0:
        return jsonify({
            "error": "trial_days cannot be negative"
        }), 400

    existing_plan = SubscriptionPlan.query.filter_by(
        variant_id=variant.id,
        billing_interval=interval
    ).first()

    if existing_plan:
        return jsonify({
            "error": "A plan already exists for this variant and billing interval"
        }), 409

    plan = SubscriptionPlan(
        variant_id=variant.id,
        plan_name=data["plan_name"].strip(),
        billing_interval=interval,
        price=price,
        trial_days=trial_days,
        description=data.get("description")
    )

    db.session.add(plan)
    db.session.commit()

    return jsonify({
        "message": "Subscription plan created successfully",
        "plan": serialize_plan(plan)
    }), 201


# GET ALL SUBSCRIPTION PLANS
@plan_bp.route("/", methods=["GET"])
def get_plans():
    plans = SubscriptionPlan.query.order_by(
        SubscriptionPlan.id.desc()
    ).all()

    return jsonify({
        "count": len(plans),
        "plans": [serialize_plan(plan) for plan in plans]
    }), 200


# GET PLAN BY ID
@plan_bp.route("/<int:plan_id>", methods=["GET"])
def get_plan(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)

    if not plan:
        return jsonify({
            "error": "Subscription plan not found"
        }), 404

    return jsonify({
        "plan": serialize_plan(plan)
    }), 200


# UPDATE SUBSCRIPTION PLAN
@plan_bp.route("/<int:plan_id>", methods=["PUT"])
def update_plan(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)

    if not plan:
        return jsonify({
            "error": "Subscription plan not found"
        }), 404

    data = request.get_json(silent=True) or {}

    if "plan_name" in data:
        if not isinstance(data["plan_name"], str) or not data["plan_name"].strip():
            return jsonify({
                "error": "plan_name cannot be empty"
            }), 400
        plan.plan_name = data["plan_name"].strip()

    if "billing_interval" in data:
        if data["billing_interval"] not in ALLOWED_INTERVALS:
            return jsonify({
                "error": "Invalid billing interval",
                "allowed_values": ALLOWED_INTERVALS
            }), 400

        duplicate = SubscriptionPlan.query.filter(
            SubscriptionPlan.variant_id == plan.variant_id,
            SubscriptionPlan.billing_interval == data["billing_interval"],
            SubscriptionPlan.id != plan.id
        ).first()

        if duplicate:
            return jsonify({
                "error": "A plan already exists for this variant and billing interval"
            }), 409

        plan.billing_interval = data["billing_interval"]

    if "price" in data:
        price = validate_price(data["price"])
        if price is None:
            return jsonify({
                "error": "Price must be a positive number"
            }), 400
        plan.price = price

    if "trial_days" in data:
        try:
            trial_days = int(data["trial_days"])
            if trial_days < 0:
                raise ValueError
            plan.trial_days = trial_days
        except (ValueError, TypeError):
            return jsonify({
                "error": "trial_days must be a non-negative integer"
            }), 400

    if "description" in data:
        plan.description = data["description"]

    db.session.commit()

    return jsonify({
        "message": "Subscription plan updated successfully",
        "plan": serialize_plan(plan)
    }), 200


# ACTIVATE / DEACTIVATE PLAN
@plan_bp.route("/<int:plan_id>/status", methods=["PATCH"])
def update_plan_status(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)

    if not plan:
        return jsonify({
            "error": "Subscription plan not found"
        }), 404

    data = request.get_json(silent=True) or {}

    if "is_active" not in data or not isinstance(data["is_active"], bool):
        return jsonify({
            "error": "is_active must be true or false"
        }), 400

    if data["is_active"] and not plan.variant.is_active:
        return jsonify({
            "error": "Cannot activate a plan whose product variant is inactive"
        }), 400

    plan.is_active = data["is_active"]
    db.session.commit()

    return jsonify({
        "message": "Subscription plan status updated successfully",
        "plan": serialize_plan(plan)
    }), 200


# DELETE SUBSCRIPTION PLAN
@plan_bp.route("/<int:plan_id>", methods=["DELETE"])
def delete_plan(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)

    if not plan:
        return jsonify({
            "error": "Subscription plan not found"
        }), 404

    db.session.delete(plan)
    db.session.commit()

    return jsonify({
        "message": "Subscription plan deleted successfully"
    }), 200
