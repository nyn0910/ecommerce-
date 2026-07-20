import hmac
import hashlib
import uuid
from flask import Blueprint, redirect, url_for, flash, request, current_app, render_template
from extensions import db
from models import CartItem, Order, OrderItem
from utils.auth import login_required, current_user
from utils.clients import get_razorpay_client

bp = Blueprint("payment", __name__, url_prefix="/payment")


@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    """Creates our Order record + a Razorpay Payment Link, then redirects the
    browser to Razorpay's hosted checkout page. No client-side JS involved —
    this is a plain HTTP redirect, same as clicking a link."""
    user = current_user()
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    total_amount = sum(float(item.product.price) * item.quantity for item in cart_items)
    reference_id = str(uuid.uuid4())

    order = Order(
        user_id=user.id,
        total_amount=total_amount,
        reference_id=reference_id,
        status="created",
    )
    db.session.add(order)
    db.session.flush()  # get order.id before commit

    for item in cart_items:
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
                owner_id=item.product.owner_id,
            )
        )
    db.session.commit()

    client = get_razorpay_client()
    payment_link = client.payment_link.create(
        {
            "amount": int(round(total_amount * 100)),  # paise
            "currency": "INR",
            "accept_partial": False,
            "description": f"Order #{order.id}",
            "customer": {"name": user.name, "email": user.email},
            "notify": {"sms": False, "email": False},
            "reference_id": reference_id,
            "callback_url": f"{current_app.config['BASE_URL']}/payment/callback",
            "callback_method": "get",
        }
    )

    order.razorpay_payment_link_id = payment_link["id"]
    db.session.commit()

    return redirect(payment_link["short_url"])


@bp.route("/callback")
def callback():
    """Razorpay redirects the user's browser here (a plain GET) after payment.
    We verify the signature server-side before trusting anything in the URL —
    this is what stops a forged 'success' redirect from creating a fake order."""
    params = {
        "razorpay_payment_id": request.args.get("razorpay_payment_id", ""),
        "razorpay_payment_link_id": request.args.get("razorpay_payment_link_id", ""),
        "razorpay_payment_link_reference_id": request.args.get("razorpay_payment_link_reference_id", ""),
        "razorpay_payment_link_status": request.args.get("razorpay_payment_link_status", ""),
    }
    signature = request.args.get("razorpay_signature", "")

    reference_id = params["razorpay_payment_link_reference_id"]
    order = Order.query.filter_by(reference_id=reference_id).first_or_404()

    payload = "|".join(
        [
            params["razorpay_payment_link_id"],
            params["razorpay_payment_link_reference_id"],
            params["razorpay_payment_link_status"],
            params["razorpay_payment_id"],
        ]
    )
    secret = current_app.config["RAZORPAY_KEY_SECRET"].encode()
    expected_signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature) or params["razorpay_payment_link_status"] != "paid":
        order.status = "failed"
        db.session.commit()
        flash("Payment verification failed. If money was deducted, contact support.", "error")
        return redirect(url_for("cart.view_cart"))

    order.status = "paid"
    order.razorpay_payment_id = params["razorpay_payment_id"]
    db.session.commit()

    # Clear the cart only after a verified payment
    CartItem.query.filter_by(user_id=order.user_id).delete()
    db.session.commit()

    flash("Payment successful! Your order has been placed.", "success")
    return redirect(url_for("orders.list_orders"))
