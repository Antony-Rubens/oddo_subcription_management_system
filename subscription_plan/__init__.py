from flask import Blueprint

plan_bp = Blueprint(
    "subscription_plans",
    __name__,
    url_prefix="/api/subscription-plans"
)

from subscription_plan import routes