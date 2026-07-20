from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import User, Order
from utils.auth import role_required, current_user

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@role_required("admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    paid_orders = Order.query.filter_by(status="paid").all()
    total_orders = len(paid_orders)
    total_sales = sum(float(o.total_amount) for o in paid_orders)
    return render_template(
        "admin/dashboard.html",
        users=users,
        total_orders=total_orders,
        total_sales=total_sales,
        user=current_user(),
    )


@bp.route("/users/<int:user_id>/role", methods=["POST"])
@role_required("admin")
def change_role(user_id):
    new_role = request.form.get("role")
    if new_role not in ("admin", "sales", "user"):
        flash("Invalid role.", "error")
        return redirect(url_for("admin.dashboard"))

    target = User.query.get_or_404(user_id)
    target.role = new_role
    db.session.commit()
    flash(f"Updated {target.name}'s role to {new_role}.", "success")
    return redirect(url_for("admin.dashboard"))
