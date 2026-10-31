from datetime import datetime, date
from extensions import db


class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    subscription_id = db.Column(db.Integer, nullable=False, index=True)
    customer_id = db.Column(db.Integer, nullable=False, index=True)
    billing_period_start = db.Column(db.Date, nullable=False)
    billing_period_end = db.Column(db.Date, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Draft", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "subscription_id", "billing_period_start", "billing_period_end",
            name="uq_invoice_subscription_period"
        ),
    )

    items = db.relationship("InvoiceItem", backref="invoice",
                            cascade="all, delete-orphan")
    payments = db.relationship("Payment", backref="invoice",
                               cascade="all, delete-orphan")


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    line_subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    line_tax = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)


class Discount(db.Model):
    __tablename__ = "discounts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage | fixed
    value = db.Column(db.Numeric(12, 2), nullable=False)
    minimum_quantity = db.Column(db.Integer, nullable=False, default=1)
    minimum_purchase = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, nullable=False, default=0)
    product_id = db.Column(db.Integer, nullable=True, index=True)
    subscription_id = db.Column(db.Integer, nullable=True, index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class DiscountApplication(db.Model):
    __tablename__ = "discount_applications"
    id = db.Column(db.Integer, primary_key=True)
    discount_id = db.Column(db.Integer, db.ForeignKey("discounts.id"), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    discount = db.relationship("Discount")
    invoice = db.relationship("Invoice")


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    payment_method = db.Column(db.String(30), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    reference = db.Column(db.String(120), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
