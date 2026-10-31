
from decimal import Decimal, InvalidOperation
from subscription_product.models import ProductVariant


from flask import request, jsonify
from extensions import db
from subscription_product import product_bp
from subscription_product.models import Product


def serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "base_price": float(product.base_price),
        "is_active": product.is_active,
        "created_at": (
            product.created_at.isoformat()
            if product.created_at else None
        )
    }


def validate_price(value):
    try:
        price = Decimal(str(value))

        if not price.is_finite() or price < 0:
            raise ValueError

        if price.as_tuple().exponent < -2:
            raise ValueError

        if price >= Decimal("100000000"):
            raise ValueError

        return price

    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Price must be a valid non-negative amount with at most 2 decimal places.")


# CREATE PRODUCT
@product_bp.route("/", methods=["POST"])
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object is required"}), 400

    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Product name is required"}), 400

    try:
        price = validate_price(data.get("base_price", 0))

        product = Product(
            name=name.strip(),
            description=data.get("description"),
            category=data.get("category"),
            base_price=price
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product": serialize_product(product)
        }), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to create product"}), 500


# GET ALL PRODUCTS
@product_bp.route("/", methods=["GET"])
def get_products():
    products = Product.query.order_by(Product.id.desc()).all()

    return jsonify([
        serialize_product(product)
        for product in products
    ]), 200


# GET PRODUCT BY ID
@product_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(serialize_product(product)), 200


# UPDATE PRODUCT
@product_bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object is required"}), 400

    try:
        if "name" in data:
            if not isinstance(data["name"], str) or not data["name"].strip():
                return jsonify({"error": "Product name cannot be empty"}), 400
            product.name = data["name"].strip()

        if "description" in data:
            product.description = data["description"]

        if "category" in data:
            product.category = data["category"]

        if "base_price" in data:
            product.base_price = validate_price(data["base_price"])

        db.session.commit()

        return jsonify({
            "message": "Product updated successfully",
            "product": serialize_product(product)
        }), 200

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to update product"}), 500


# ACTIVATE / DEACTIVATE PRODUCT
@product_bp.route("/<int:product_id>/status", methods=["PATCH"])
def update_product_status(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not isinstance(data.get("is_active"), bool):
        return jsonify({
            "error": "is_active must be true or false"
        }), 400

    product.is_active = data["is_active"]
    db.session.commit()

    return jsonify({
        "message": "Product status updated successfully",
        "product": serialize_product(product)
    }), 200


# DELETE PRODUCT
@product_bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product.variants:
        return jsonify({
            "error": "Cannot delete product with existing variants. Deactivate it instead."
        }), 409

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Product deleted successfully"
    }), 200



def serialize_variant(variant):
    return {
        "id": variant.id,
        "product_id": variant.product_id,
        "variant_name": variant.variant_name,
        "attributes": variant.attributes,
        "price": float(variant.price),
        "is_active": variant.is_active
    }


def validate_variant_price(value):
    from decimal import Decimal, InvalidOperation

    try:
        price = Decimal(str(value))

        if (
            not price.is_finite()
            or price < 0
            or price >= Decimal("100000000")
            or price.as_tuple().exponent < -2
        ):
            raise ValueError

        return price

    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(
            "Price must be non-negative with at most 2 decimal places."
        )


# CREATE PRODUCT VARIANT
@product_bp.route("/<int:product_id>/variants", methods=["POST"])
def create_variant(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if not product.is_active:
        return jsonify({"error": "Cannot add variants to an inactive product"}), 409

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object is required"}), 400

    name = data.get("variant_name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Variant name is required"}), 400

    attributes = data.get("attributes", {})

    if not isinstance(attributes, dict):
        return jsonify({"error": "Attributes must be a JSON object"}), 400

    try:
        price = validate_variant_price(data.get("price"))

        existing = ProductVariant.query.filter_by(
            product_id=product_id,
            variant_name=name.strip()
        ).first()

        if existing:
            return jsonify({"error": "Variant already exists"}), 409

        variant = ProductVariant(
            product_id=product_id,
            variant_name=name.strip(),
            attributes=attributes,
            price=price
        )

        db.session.add(variant)
        db.session.commit()

        return jsonify({
            "message": "Variant created successfully",
            "variant": serialize_variant(variant)
        }), 201

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to create variant"}), 500


# GET ALL VARIANTS OF A PRODUCT
@product_bp.route("/<int:product_id>/variants", methods=["GET"])
def get_variants(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    variants = ProductVariant.query.filter_by(
        product_id=product_id
    ).order_by(ProductVariant.id).all()

    return jsonify([
        serialize_variant(variant)
        for variant in variants
    ]), 200


# GET VARIANT BY ID
@product_bp.route("/variants/<int:variant_id>", methods=["GET"])
def get_variant(variant_id):
    variant = db.session.get(ProductVariant, variant_id)

    if not variant:
        return jsonify({"error": "Variant not found"}), 404

    return jsonify(serialize_variant(variant)), 200


# UPDATE VARIANT
@product_bp.route("/variants/<int:variant_id>", methods=["PUT"])
def update_variant(variant_id):
    variant = db.session.get(ProductVariant, variant_id)

    if not variant:
        return jsonify({"error": "Variant not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON object is required"}), 400

    try:
        if "variant_name" in data:
            name = data["variant_name"]

            if not isinstance(name, str) or not name.strip():
                return jsonify({"error": "Variant name cannot be empty"}), 400

            duplicate = ProductVariant.query.filter(
                ProductVariant.product_id == variant.product_id,
                ProductVariant.variant_name == name.strip(),
                ProductVariant.id != variant_id
            ).first()

            if duplicate:
                return jsonify({"error": "Variant name already exists"}), 409

            variant.variant_name = name.strip()

        if "price" in data:
            variant.price = validate_variant_price(data["price"])

        if "attributes" in data:
            if not isinstance(data["attributes"], dict):
                return jsonify({"error": "Attributes must be a JSON object"}), 400
            variant.attributes = data["attributes"]

        db.session.commit()

        return jsonify({
            "message": "Variant updated successfully",
            "variant": serialize_variant(variant)
        }), 200

    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Unable to update variant"}), 500


# ACTIVATE / DEACTIVATE VARIANT
@product_bp.route("/variants/<int:variant_id>/status", methods=["PATCH"])
def update_variant_status(variant_id):
    variant = db.session.get(ProductVariant, variant_id)

    if not variant:
        return jsonify({"error": "Variant not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not isinstance(data.get("is_active"), bool):
        return jsonify({"error": "is_active must be true or false"}), 400

    if data["is_active"] and not variant.product.is_active:
        return jsonify({"error": "Cannot activate a variant of an inactive product"}), 409

    variant.is_active = data["is_active"]
    db.session.commit()

    return jsonify({
        "message": "Variant status updated successfully",
        "variant": serialize_variant(variant)
    }), 200


# DELETE VARIANT
@product_bp.route("/variants/<int:variant_id>", methods=["DELETE"])
def delete_variant(variant_id):
    variant = db.session.get(ProductVariant, variant_id)

    if not variant:
        return jsonify({"error": "Variant not found"}), 404

    db.session.delete(variant)
    db.session.commit()

    return jsonify({
        "message": "Variant deleted successfully"
    }), 200
