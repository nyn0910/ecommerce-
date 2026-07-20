from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import CartItem, Product
from utils.auth import login_required, current_user

bp = Blueprint("cart", __name__, url_prefix="/cart")


@bp.route("/")
@login_required
def view_cart():
    user = current_user()
    items = CartItem.query.filter_by(user_id=user.id).all()
    total = sum(float(item.product.price) * item.quantity for item in items)
    return render_template("cart.html", items=items, total=total, user=user)


@bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    user = current_user()
    Product.query.get_or_404(product_id)  # 404 if product doesn't exist

    item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=user.id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()
    flash("Added to cart.", "success")

    # Send the user back wherever they came from (product list or detail page)
    return redirect(request.referrer or url_for("products.list_products"))


@bp.route("/update/<int:item_id>", methods=["POST"])
@login_required
def update(item_id):
    user = current_user()
    item = CartItem.query.filter_by(id=item_id, user_id=user.id).first_or_404()

    quantity = int(request.form.get("quantity", 1))
    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity
    db.session.commit()
    return redirect(url_for("cart.view_cart"))


@bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove(item_id):
    user = current_user()
    item = CartItem.query.filter_by(id=item_id, user_id=user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Removed from cart.", "success")
    return redirect(url_for("cart.view_cart"))
