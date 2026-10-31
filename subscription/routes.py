
from datetime import date, datetime
from decimal import Decimal

from flask import request, jsonify

from extensions import db
from subscription import subscription_bp
from subscription.models import Subscription
from subscription_plan.models import SubscriptionPlan


def serialize_subscription(subscription):
    return {
        "id": subscription.id,
        "customer_id": subscription.customer_id,
        "plan_id": subscription.plan_id,
        "plan_name": subscription.plan.plan_name,
        "billing_interval": subscription.plan.billing_interval,
        "unit_price": float(subscription.plan.price),
        "quantity": subscription.quantity,
        "total_price": float(
            Decimal(str(subscription.plan.price)) *
            subscription.quantity
        ),
        "status": subscription.status,
        "start_date": subscription.start_date.isoformat(),
        "next_billing_date": (
            subscription.next_billing_date.isoformat()
            if subscription.next_billing_date else None
        ),
        "end_date": (
            subscription.end_date.isoformat()
            if subscription.end_date else None
        ),
        "paused_at": (
            subscription.paused_at.isoformat()
            if subscription.paused_at else None
        ),
        "remaining_days": subscription.remaining_days,
        "created_at": (
            subscription.created_at.isoformat()
            if subscription.created_at else None
        )
    }


# CREATE SUBSCRIPTION
@subscription_bp.route("/", methods=["POST"])
def create_subscription():
    data = request.get_json(silent=True) or {}

    required_fields = ["customer_id", "plan_id", "start_date"]

    for field in required_fields:
        if data.get(field) in (None, ""):
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        customer_id = int(data["customer_id"])
        plan_id = int(data["plan_id"])
        quantity = int(data.get("quantity", 1))
        start_date = date.fromisoformat(data["start_date"])
    except (ValueError, TypeError):
        return jsonify({
            "error": "Invalid customer_id, plan_id, quantity or start_date"
        }), 400

    if customer_id <= 0 or quantity <= 0:
        return jsonify({
            "error": "customer_id and quantity must be positive integers"
        }), 400

    plan = db.session.get(SubscriptionPlan, plan_id)

    if not plan:
        return jsonify({
            "error": "Subscription plan not found"
        }), 404

    if not plan.is_active:
        return jsonify({
            "error": "Cannot subscribe to an inactive plan"
        }), 400

    if not plan.variant.is_active:
        return jsonify({
            "error": "The product variant associated with this plan is inactive"
        }), 400

    subscription = Subscription(
        customer_id=customer_id,
        plan_id=plan_id,
        quantity=quantity,
        status="draft",
        start_date=start_date
    )

    db.session.add(subscription)
    db.session.commit()

    return jsonify({
        "message": "Subscription created successfully",
        "subscription": serialize_subscription(subscription)
    }), 201


# GET ALL SUBSCRIPTIONS
@subscription_bp.route("/", methods=["GET"])
def get_subscriptions():
    subscriptions = Subscription.query.order_by(
        Subscription.id.desc()
    ).all()

    return jsonify({
        "count": len(subscriptions),
        "subscriptions": [
            serialize_subscription(item)
            for item in subscriptions
        ]
    }), 200


# GET SUBSCRIPTION BY ID
@subscription_bp.route("/<int:subscription_id>", methods=["GET"])
def get_subscription(subscription_id):
    subscription = db.session.get(
        Subscription,
        subscription_id
    )

    if not subscription:
        return jsonify({
            "error": "Subscription not found"
        }), 404

    return jsonify({
        "subscription": serialize_subscription(subscription)
    }), 200
