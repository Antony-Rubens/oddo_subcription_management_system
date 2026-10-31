from billing.routes import billing_bp


def init_billing(app):
    app.register_blueprint(billing_bp)
