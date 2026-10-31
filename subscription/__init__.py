from flask import Blueprint

subscription_bp = Blueprint(
    "subscriptions",
    __name__,
    url_prefix="/api/subscriptions"
)

from subscription import routes