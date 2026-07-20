from datetime import datetime
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)  # never plain text
    role = db.Column(db.Enum("admin", "sales", "user", name="role_enum"), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship("Product", backref="owner", lazy=True)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    stock = db.Column(db.Integer, default=10)
    image_url = db.Column(db.String(500), nullable=False)  # Cloudinary URL only
    image_public_id = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    product = db.relationship("Product")


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    product = db.relationship("Product")


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    reference_id = db.Column(db.String(64), unique=True, nullable=False)  # our own ref, sent to Razorpay
    razorpay_payment_link_id = db.Column(db.String(120))
    razorpay_payment_id = db.Column(db.String(120))
    status = db.Column(db.Enum("created", "paid", "failed", name="order_status_enum"), default="created")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    name = db.Column(db.String(200))
    price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # seller at time of purchase
