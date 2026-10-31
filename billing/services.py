from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import IntegrityError
from extensions import db
from billing.models import Invoice, InvoiceItem, Discount, DiscountApplication, Payment

CENT = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_status(invoice):
    if invoice.amount_paid >= invoice.total_amount and invoice.total_amount > 0:
        return "Paid"
    if invoice.due_date < date.today() and invoice.amount_paid < invoice.total_amount:
        return "Overdue"
    return invoice.status if invoice.status in ("Draft", "Confirmed", "Cancelled") else "Confirmed"


def invoice_dict(inv):
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "subscription_id": inv.subscription_id,
        "customer_id": inv.customer_id,
        "billing_period_start": inv.billing_period_start.isoformat(),
        "billing_period_end": inv.billing_period_end.isoformat(),
        "invoice_date": inv.invoice_date.isoformat(),
        "due_date": inv.due_date.isoformat(),
        "subtotal": str(inv.subtotal),
        "discount_amount": str(inv.discount_amount),
        "tax_amount": str(inv.tax_amount),
        "total_amount": str(inv.total_amount),
        "amount_paid": str(inv.amount_paid),
        "balance_due": str(money(inv.total_amount - inv.amount_paid)),
        "status": invoice_status(inv),
        "items": [{
            "id": x.id, "product_id": x.product_id, "description": x.description,
            "quantity": x.quantity, "unit_price": str(x.unit_price),
            "tax_rate": str(x.tax_rate), "line_subtotal": str(x.line_subtotal),
            "line_tax": str(x.line_tax), "line_total": str(x.line_total)
        } for x in inv.items],
        "payments": [{
            "id": p.id, "payment_method": p.payment_method, "amount": str(p.amount),
            "payment_date": p.payment_date.isoformat(),
            "reference": p.reference, "note": p.note
        } for p in inv.payments]
    }


def create_invoice(data):
    required = ["subscription_id", "customer_id", "billing_period_start",
                "billing_period_end", "due_date", "items"]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    if not isinstance(data["items"], list) or not data["items"]:
        raise ValueError("items must be a non-empty list")

    start = date.fromisoformat(data["billing_period_start"])
    end = date.fromisoformat(data["billing_period_end"])
    due = date.fromisoformat(data["due_date"])
    if end < start:
        raise ValueError("billing_period_end must be on or after billing_period_start")

    existing = Invoice.query.filter_by(
        subscription_id=int(data["subscription_id"]),
        billing_period_start=start,
        billing_period_end=end
    ).first()
    if existing:
        raise ValueError(f"Invoice already exists for this subscription and billing period: {existing.invoice_number}")

    subtotal = Decimal("0.00")
    tax_total = Decimal("0.00")
    prepared = []
    for row in data["items"]:
        qty = int(row.get("quantity", 1))
        price = money(row.get("unit_price", 0))
        tax_rate = Decimal(str(row.get("tax_rate", 0)))
        if qty <= 0 or price < 0 or tax_rate < 0:
            raise ValueError("Quantity must be positive; price and tax rate cannot be negative")
        line_subtotal = money(price * qty)
        line_tax = money(line_subtotal * tax_rate / Decimal("100"))
        line_total = money(line_subtotal + line_tax)
        subtotal += line_subtotal
        tax_total += line_tax
        prepared.append((row, qty, price, tax_rate, line_subtotal, line_tax, line_total))

    subtotal = money(subtotal)
    tax_total = money(tax_total)
    discount_total = Decimal("0.00")
    today = date.today()
    discounts = Discount.query.filter_by(active=True).filter(
        Discount.start_date <= today, Discount.end_date >= today
    ).order_by(Discount.id.asc()).all()

    total_qty = sum(x[1] for x in prepared)
    for disc in discounts:
        if disc.usage_limit is not None and disc.times_used >= disc.usage_limit:
            continue
        if total_qty < disc.minimum_quantity or subtotal < money(disc.minimum_purchase):
            continue
        if disc.subscription_id is not None and disc.subscription_id != int(data["subscription_id"]):
            continue
        if disc.product_id is not None and not any(x[0].get("product_id") == disc.product_id for x in prepared):
            continue
        if disc.discount_type == "percentage":
            amount = money(subtotal * Decimal(str(disc.value)) / Decimal("100"))
        elif disc.discount_type == "fixed":
            amount = money(disc.value)
        else:
            continue
        amount = min(amount, money(subtotal - discount_total))
        if amount <= 0:
            continue
        discount_total += amount
        # Apply at most one matching rule to avoid unexpected stacking.
        break

    total = money(subtotal - discount_total + tax_total)
    number = "INV-" + date.today().strftime("%Y%m%d") + "-" + str(Invoice.query.count() + 1).zfill(5)
    inv = Invoice(
        invoice_number=number,
        subscription_id=int(data["subscription_id"]),
        customer_id=int(data["customer_id"]),
        billing_period_start=start,
        billing_period_end=end,
        invoice_date=today,
        due_date=due,
        subtotal=subtotal,
        discount_amount=discount_total,
        tax_amount=tax_total,
        total_amount=total,
        amount_paid=Decimal("0.00"),
        status="Draft"
    )
    for row, qty, price, rate, line_sub, line_tax, line_total in prepared:
        inv.items.append(InvoiceItem(
            product_id=row.get("product_id"),
            description=row.get("description") or "Subscription item",
            quantity=qty, unit_price=price, tax_rate=rate,
            line_subtotal=line_sub, line_tax=line_tax, line_total=line_total
        ))
    db.session.add(inv)
    try:
        db.session.flush()
        if discount_total > 0:
            disc = next((d for d in discounts
                         if (d.usage_limit is None or d.times_used < d.usage_limit)
                         and (d.subscription_id is None or d.subscription_id == inv.subscription_id)
                         and (d.product_id is None or any(x.product_id == d.product_id for x in inv.items))), None)
            if disc:
                disc.times_used += 1
                db.session.add(DiscountApplication(
                    discount_id=disc.id, invoice_id=inv.id, amount=discount_total
                ))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("An invoice already exists for this subscription and billing period")
    except Exception:
        db.session.rollback()
        raise
    return inv


def record_payment(invoice, data):
    amount = money(data.get("amount", 0))
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")
    if invoice.status == "Cancelled":
        raise ValueError("Cannot record payment against a cancelled invoice")
    balance = money(invoice.total_amount - invoice.amount_paid)
    if amount > balance:
        raise ValueError(f"Payment exceeds outstanding balance of {balance}")
    method = (data.get("payment_method") or "").strip()
    if not method:
        raise ValueError("payment_method is required")
    payment_date = date.fromisoformat(data["payment_date"]) if data.get("payment_date") else date.today()
    payment = Payment(
        invoice_id=invoice.id, payment_method=method, amount=amount,
        payment_date=payment_date, reference=data.get("reference"), note=data.get("note")
    )
    invoice.amount_paid = money(invoice.amount_paid + amount)
    invoice.status = "Paid" if invoice.amount_paid >= invoice.total_amount else "Confirmed"
    db.session.add(payment)
    db.session.commit()
    return payment
