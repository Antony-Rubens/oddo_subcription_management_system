from datetime import date
from decimal import Decimal
from flask import Blueprint, request, jsonify
from extensions import db
from billing.models import Invoice, Discount, Payment
from billing.services import create_invoice, invoice_dict, record_payment, money

billing_bp = Blueprint("billing", __name__, url_prefix="/api/billing")


def error(message, code=400):
    return jsonify({"status": "error", "message": str(message)}), code


@billing_bp.route("/invoices", methods=["POST"])
def generate_invoice():
    try:
        inv = create_invoice(request.get_json(silent=True) or {})
        return jsonify({"status": "success", "message": "Invoice generated",
                        "invoice": invoice_dict(inv)}), 201
    except ValueError as exc:
        db.session.rollback()
        return error(exc, 409 if "already exists" in str(exc) else 400)
    except Exception as exc:
        db.session.rollback()
        return error(exc, 500)


@billing_bp.route("/invoices", methods=["GET"])
def list_invoices():
    query = Invoice.query
    status = request.args.get("status")
    customer_id = request.args.get("customer_id", type=int)
    subscription_id = request.args.get("subscription_id", type=int)
    if status:
        query = query.filter(Invoice.status == status)
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if subscription_id:
        query = query.filter(Invoice.subscription_id == subscription_id)
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)
    pagination = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        "status": "success", "page": page, "per_page": per_page,
        "total": pagination.total,
        "invoices": [invoice_dict(x) for x in pagination.items]
    })


@billing_bp.route("/invoices/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    inv = db.session.get(Invoice, invoice_id)
    if not inv:
        return error("Invoice not found", 404)
    return jsonify({"status": "success", "invoice": invoice_dict(inv)})


@billing_bp.route("/invoices/<int:invoice_id>/confirm", methods=["POST"])
def confirm_invoice(invoice_id):
    inv = db.session.get(Invoice, invoice_id)
    if not inv:
        return error("Invoice not found", 404)
    if inv.status != "Draft":
        return error("Only Draft invoices can be confirmed")
    inv.status = "Confirmed"
    db.session.commit()
    return jsonify({"status": "success", "invoice": invoice_dict(inv)})


@billing_bp.route("/invoices/<int:invoice_id>/cancel", methods=["POST"])
def cancel_invoice(invoice_id):
    inv = db.session.get(Invoice, invoice_id)
    if not inv:
        return error("Invoice not found", 404)
    if inv.amount_paid > 0:
        return error("An invoice with payments cannot be cancelled")
    inv.status = "Cancelled"
    db.session.commit()
    return jsonify({"status": "success", "message": "Invoice cancelled"})


@billing_bp.route("/invoices/<int:invoice_id>/payments", methods=["POST"])
def add_payment(invoice_id):
    inv = db.session.get(Invoice, invoice_id)
    if not inv:
        return error("Invoice not found", 404)
    try:
        payment = record_payment(inv, request.get_json(silent=True) or {})
        return jsonify({"status": "success", "message": "Payment recorded",
                        "payment_id": payment.id, "invoice": invoice_dict(inv)}), 201
    except ValueError as exc:
        db.session.rollback()
        return error(exc)
    except Exception as exc:
        db.session.rollback()
        return error(exc, 500)


@billing_bp.route("/payments", methods=["GET"])
def list_payments():
    query = Payment.query
    invoice_id = request.args.get("invoice_id", type=int)
    if invoice_id:
        query = query.filter_by(invoice_id=invoice_id)
    rows = query.order_by(Payment.payment_date.desc()).limit(500).all()
    return jsonify({"status": "success", "payments": [{
        "id": p.id, "invoice_id": p.invoice_id, "payment_method": p.payment_method,
        "amount": str(p.amount), "payment_date": p.payment_date.isoformat(),
        "reference": p.reference, "note": p.note
    } for p in rows]})


@billing_bp.route("/discounts", methods=["POST"])
def create_discount():
    data = request.get_json(silent=True) or {}
    try:
        name = (data.get("name") or "").strip()
        kind = data.get("discount_type")
        value = money(data.get("value", 0))
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
        if not name:
            raise ValueError("name is required")
        if kind not in ("percentage", "fixed"):
            raise ValueError("discount_type must be percentage or fixed")
        if value <= 0 or (kind == "percentage" and value > 100):
            raise ValueError("Invalid discount value")
        if end < start:
            raise ValueError("end_date must be on or after start_date")
        limit = data.get("usage_limit")
        if limit is not None and int(limit) < 1:
            raise ValueError("usage_limit must be positive")
        disc = Discount(
            name=name, discount_type=kind, value=value,
            minimum_quantity=int(data.get("minimum_quantity", 1)),
            minimum_purchase=money(data.get("minimum_purchase", 0)),
            start_date=start, end_date=end,
            usage_limit=int(limit) if limit is not None else None,
            product_id=data.get("product_id"),
            subscription_id=data.get("subscription_id"),
            active=bool(data.get("active", True))
        )
        if disc.minimum_quantity < 1 or disc.minimum_purchase < 0:
            raise ValueError("Minimum quantity must be at least 1 and purchase cannot be negative")
        db.session.add(disc)
        db.session.commit()
        return jsonify({"status": "success", "discount_id": disc.id,
                        "message": "Discount created"}), 201
    except (ValueError, KeyError, TypeError) as exc:
        db.session.rollback()
        return error(exc)
    except Exception as exc:
        db.session.rollback()
        return error(exc, 500)


@billing_bp.route("/discounts", methods=["GET"])
def list_discounts():
    rows = Discount.query.order_by(Discount.id.desc()).all()
    return jsonify({"status": "success", "discounts": [{
        "id": d.id, "name": d.name, "discount_type": d.discount_type,
        "value": str(d.value), "minimum_quantity": d.minimum_quantity,
        "minimum_purchase": str(d.minimum_purchase),
        "start_date": d.start_date.isoformat(), "end_date": d.end_date.isoformat(),
        "usage_limit": d.usage_limit, "times_used": d.times_used,
        "product_id": d.product_id, "subscription_id": d.subscription_id,
        "active": d.active
    } for d in rows]})


@billing_bp.route("/discounts/<int:discount_id>", methods=["PATCH"])
def update_discount(discount_id):
    disc = db.session.get(Discount, discount_id)
    if not disc:
        return error("Discount not found", 404)
    data = request.get_json(silent=True) or {}
    if "active" in data:
        disc.active = bool(data["active"])
    if "end_date" in data:
        disc.end_date = date.fromisoformat(data["end_date"])
    if "usage_limit" in data:
        disc.usage_limit = int(data["usage_limit"]) if data["usage_limit"] is not None else None
    db.session.commit()
    return jsonify({"status": "success", "message": "Discount updated"})


@billing_bp.route("/dashboard", methods=["GET"])
def dashboard():
    today = date.today()
    all_invoices = Invoice.query.filter(Invoice.status != "Cancelled").all()
    active_count = sum(1 for x in all_invoices if x.status in ("Draft", "Confirmed", "Overdue"))
    revenue = sum((Decimal(str(x.amount_paid)) for x in all_invoices), Decimal("0"))
    outstanding = sum((max(Decimal("0"), Decimal(str(x.total_amount)) -
                                  Decimal(str(x.amount_paid))) for x in all_invoices),
                      Decimal("0"))
    overdue = [x for x in all_invoices
               if x.due_date < today and x.amount_paid < x.total_amount]
    return jsonify({
        "status": "success",
        "summary": {
            "invoice_count": len(all_invoices),
            "active_unpaid_invoices": active_count,
            "revenue_received": str(money(revenue)),
            "outstanding_amount": str(money(outstanding)),
            "overdue_invoice_count": len(overdue),
            "overdue_amount": str(money(sum(
                (Decimal(str(x.total_amount)) - Decimal(str(x.amount_paid)) for x in overdue),
                Decimal("0")
            )))
        },
        "overdue_invoices": [{
            "id": x.id, "invoice_number": x.invoice_number,
            "customer_id": x.customer_id, "due_date": x.due_date.isoformat(),
            "balance_due": str(money(x.total_amount - x.amount_paid))
        } for x in overdue]
    })
