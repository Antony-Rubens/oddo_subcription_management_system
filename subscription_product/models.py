from extensions import db
from datetime import datetime


class Product(db.Model):

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text)

    category = db.Column(db.String(100))

    base_price = db.Column(db.Numeric(10, 2), nullable=False)

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    variants = db.relationship(
        "ProductVariant",
        backref="product",
        cascade="all, delete-orphan"
    )


class ProductVariant(db.Model):

    __tablename__ = "product_variants"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    variant_name = db.Column(
        db.String(150),
        nullable=False
    )

    attributes = db.Column(db.JSON)

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )