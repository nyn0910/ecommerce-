from flask import Blueprint, render_template
from models import Order, OrderItem
from utils.auth import login_required, current_user

bp = Blueprint("orders", __name__, url_prefix="/orders")


@bp.route("/")
@login_required
def list_orders():
    user = current_user()

    if user.role == "admin":
        orders = Order.query.filter_by(status="paid").order_by(Order.created_at.desc()).all()
    elif user.role == "sales":
        # Only orders that contain at least one of this seller's products
        order_ids = (
            OrderItem.query.filter_by(owner_id=user.id)
            .with_entities(OrderItem.order_id)
            .distinct()
            .all()
        )
        order_ids = [oid for (oid,) in order_ids]
        orders = (
            Order.query.filter(Order.id.in_(order_ids), Order.status == "paid")
            .order_by(Order.created_at.desc())
            .all()
        )
    else:
        orders = (
            Order.query.filter_by(user_id=user.id, status="paid")
            .order_by(Order.created_at.desc())
            .all()
        )

    return render_template("orders.html", orders=orders, user=user)
