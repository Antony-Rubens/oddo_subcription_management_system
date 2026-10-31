# Brightloop Billing — Member 2

## Scope
Invoices, invoice lines, discounts, discount applications, payments, invoice status tracking and billing dashboard.

## Install dependencies
Activate your virtual environment, then run:
```powershell
pip install Flask Flask-SQLAlchemy PyMySQL python-dotenv
```

## Environment
Ensure `.env` contains:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD="YOUR_MYSQL_PASSWORD"
DB_NAME=odoo
```
Do not commit `.env` or share the real password.

## Run
```powershell
python app.py
```
The app imports billing models and calls `db.create_all()`. This creates missing tables; it does not migrate existing table structures.

Verify in MySQL Workbench:
```sql
USE odoo;
SHOW TABLES;
```
Expected tables: `invoices`, `invoice_items`, `discounts`, `discount_applications`, `payments`.

## API endpoints
- `POST /api/billing/invoices` — generate invoice from subscription/customer IDs and supplied subscription line snapshot.
- `GET /api/billing/invoices` — list invoices; optional `status`, `customer_id`, `subscription_id`, `page`, `per_page`.
- `GET /api/billing/invoices/<id>` — invoice detail.
- `POST /api/billing/invoices/<id>/confirm` — Draft to Confirmed.
- `POST /api/billing/invoices/<id>/cancel` — cancel unpaid invoice.
- `POST /api/billing/invoices/<id>/payments` — record a payment.
- `GET /api/billing/payments` — list payments; optional `invoice_id`.
- `POST /api/billing/discounts` — create discount.
- `GET /api/billing/discounts` — list discounts.
- `PATCH /api/billing/discounts/<id>` — update active/end_date/usage_limit.
- `GET /api/billing/dashboard` — billing summary and overdue invoices.

## Example: create a discount
```json
{
  "name": "10 percent seat discount",
  "discount_type": "percentage",
  "value": 10,
  "minimum_quantity": 5,
  "minimum_purchase": 0,
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "usage_limit": 100
}
```
`discount_type` is `percentage` or `fixed`. Optional `product_id` and `subscription_id` limit the rule's scope.

## Example: generate an invoice
The subscription module should call this endpoint with a snapshot of the subscription's billable lines. Amounts are recalculated by this billing service; do not trust client-supplied totals.
```json
{
  "subscription_id": 12,
  "customer_id": 4,
  "billing_period_start": "2026-10-01",
  "billing_period_end": "2026-10-31",
  "due_date": "2026-11-07",
  "items": [
    {
      "product_id": 3,
      "description": "Business plan — 5 seats",
      "quantity": 5,
      "unit_price": 500,
      "tax_rate": 18
    }
  ]
}
```
The API prevents a second invoice for the same subscription and billing-period dates. A database unique constraint backs up the check.

## Example: record payment
```json
{
  "payment_method": "Bank Transfer",
  "amount": 2950,
  "payment_date": "2026-10-31",
  "reference": "BANK-REF-001",
  "note": "October subscription payment"
}
```
Use the invoice ID in `/api/billing/invoices/<id>/payments`.

## Important integration notes
- This implementation deliberately does not add foreign keys to `subscriptions`, `customers` or `products`, because those tables are owned by other team members and are not present in the current project. IDs are stored as references and can be linked once the shared schema is integrated.
- The invoice endpoint accepts subscription line snapshots. The subscription owner must call it at billing time and provide the current customer, period and lines.
- Tax rates are supplied per invoice line from the product/tax module. This code calculates tax; it does not define the admin tax-rule management module.
- Discount rules are applied automatically during invoice creation. One eligible rule is applied per invoice (no stacking); first eligible rule by ID wins.
- Dashboard `revenue_received` is recorded payments, not recognized accounting revenue or MRR.
- Authentication/role checks are not included in this module because the current app has no auth integration yet. Restrict discount creation/updates and invoice actions to authorized roles when the auth module is connected.
- `db.create_all()` is suitable for initial local development only. Use Flask-Migrate/Alembic for schema changes after deployment.
- Before production, add transaction locking around discount usage and invoice/payment updates to prevent race conditions under concurrent requests.
