
from datetime import datetime
from extensions import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)

    # Reference to the Customer module
    customer_id = db.Column(db.Integer, nullable=False)

    # Link to the selected subscription plan
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("subscription_plans.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    status = db.Column(
        db.Enum("draft", "active", "paused", "closed"),
        nullable=False,
        default="draft"
    )

    start_date = db.Column(db.Date, nullable=False)

    next_billing_date = db.Column(db.Date, nullable=True)

    end_date = db.Column(db.Date, nullable=True)

    paused_at = db.Column(db.DateTime, nullable=True)

    remaining_days = db.Column(db.Integer, nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    plan = db.relationship(
        "SubscriptionPlan",
        backref="subscriptions"
    )
