import cloudinary.uploader
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from extensions import db
from models import Product
from utils.auth import current_user, role_required

bp = Blueprint("products", __name__, url_prefix="/products")


@bp.route("/")
def list_products():
    keyword = request.args.get("keyword", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")

    query = Product.query

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Product.name.ilike(like), Product.description.ilike(like)))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if min_price:
        query = query.filter(Product.price >= float(min_price))
    if max_price:
        query = query.filter(Product.price <= float(max_price))

    products = query.order_by(Product.created_at.desc()).all()

    return render_template(
        "products/list.html",
        products=products,
        keyword=keyword,
        category=category,
        min_price=min_price,
        max_price=max_price,
        user=current_user(),
    )


@bp.route("/<int:product_id>")
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("products/detail.html", product=product, user=current_user())


@bp.route("/new", methods=["GET", "POST"])
@role_required("admin", "sales")
def new():
    if request.method == "POST":
        return _save_product(None)
    return render_template("products/form.html", product=None)


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@role_required("admin", "sales")
def edit(product_id):
    product = Product.query.get_or_404(product_id)
    user = current_user()

    # Backend-enforced ownership check: a Sales Person may only touch their own products
    if user.role == "sales" and product.owner_id != user.id:
        abort(403)

    if request.method == "POST":
        return _save_product(product)
    return render_template("products/form.html", product=product)


@bp.route("/<int:product_id>/delete", methods=["POST"])
@role_required("admin", "sales")
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    user = current_user()

    if user.role == "sales" and product.owner_id != user.id:
        abort(403)

    if product.image_public_id:
        cloudinary.uploader.destroy(product.image_public_id)

    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "success")
    return redirect(url_for("products.list_products"))


def _save_product(product):
    """Shared create/update logic. `product` is None for create."""
    user = current_user()

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "")
    category = request.form.get("category", "").strip()
    stock = request.form.get("stock", "10")
    image_file = request.files.get("image")

    if not name or not price or not category:
        flash("Name, price and category are required.", "error")
        return render_template("products/form.html", product=product)

    image_url = product.image_url if product else None
    image_public_id = product.image_public_id if product else None

    if image_file and image_file.filename:
        # File goes straight to Cloudinary; only the returned URL is ever stored in MySQL
        result = cloudinary.uploader.upload(image_file, folder="ecommerce-products")
        image_url = result["secure_url"]
        image_public_id = result["public_id"]
    elif not product:
        flash("Product image is required.", "error")
        return render_template("products/form.html", product=product)

    if product is None:
        product = Product(owner_id=user.id)
        db.session.add(product)

    product.name = name
    product.description = description
    product.price = price
    product.category = category
    product.stock = stock or 0
    product.image_url = image_url
    product.image_public_id = image_public_id

    db.session.commit()
    flash("Product saved.", "success")
    return redirect(url_for("products.list_products"))
