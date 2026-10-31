
from datetime import datetime
from extensions import db


class SubscriptionPlan(db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.Integer, primary_key=True)

    variant_id = db.Column(
        db.Integer,
        db.ForeignKey("product_variants.id"),
        nullable=False
    )

    plan_name = db.Column(db.String(150), nullable=False)

    billing_interval = db.Column(
        db.Enum("monthly", "quarterly", "half_yearly", "yearly"),
        nullable=False
    )

    price = db.Column(db.Numeric(10, 2), nullable=False)

    trial_days = db.Column(db.Integer, default=0)

    description = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    variant = db.relationship("ProductVariant", backref="subscription_plans")
