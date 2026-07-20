from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import WishlistItem, Product
from utils.auth import login_required, current_user

bp = Blueprint("wishlist", __name__, url_prefix="/wishlist")


@bp.route("/")
@login_required
def view_wishlist():
    user = current_user()
    items = WishlistItem.query.filter_by(user_id=user.id).all()
    return render_template("wishlist.html", items=items, user=user)


@bp.route("/add/<int:product_id>", methods=["POST"])
@login_required
def add(product_id):
    user = current_user()
    Product.query.get_or_404(product_id)

    exists = WishlistItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if not exists:
        db.session.add(WishlistItem(user_id=user.id, product_id=product_id))
        db.session.commit()
    flash("Added to wishlist.", "success")
    return redirect(request.referrer or url_for("products.list_products"))


@bp.route("/remove/<int:item_id>", methods=["POST"])
@login_required
def remove(item_id):
    user = current_user()
    item = WishlistItem.query.filter_by(id=item_id, user_id=user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Removed from wishlist.", "success")
    return redirect(url_for("wishlist.view_wishlist"))
