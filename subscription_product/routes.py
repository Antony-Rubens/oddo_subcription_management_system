from flask import request, jsonify
from extensions import db
from subscription_product import product_bp
from subscription_product.models import Product


@product_bp.route("/", methods=["POST"])
def create_product():

    data = request.get_json()

    if not data or not data.get("name"):
        return jsonify({
            "error": "Product name is required"
        }), 400

    try:
        product = Product(
            name=data["name"],
            description=data.get("description"),
            category=data.get("category"),
            base_price=data.get("base_price", 0)
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except (ValueError, TypeError):
        db.session.rollback()
        return jsonify({"error": "Invalid product data"}), 400


@product_bp.route("/", methods=["GET"])
def get_products():

    products = Product.query.all()

    result = []

    for product in products:

        result.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "base_price": float(product.base_price),
            "is_active": product.is_active
        })

    return jsonify(result)