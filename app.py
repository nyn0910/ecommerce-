from flask import Flask, render_template
from config import Config
from extensions import db
from utils.clients import init_cloudinary
from utils.auth import current_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    init_cloudinary(app)

    from routes.auth import bp as auth_bp
    from routes.products import bp as products_bp
    from routes.cart import bp as cart_bp
    from routes.wishlist import bp as wishlist_bp
    from routes.orders import bp as orders_bp
    from routes.payment import bp as payment_bp
    from routes.admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)

    # Makes {{ user }} available in every template without repeating it in each view
    @app.context_processor
    def inject_user():
        return {"nav_user": current_user()}

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have permission to do that."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
