from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("register.html")

        # New accounts always start as "user" — never trust a role field
        # submitted from a public form. Admins are promoted later, server-side.
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="user",
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["role"] = user.role
        session["name"] = user.name
        flash("Account created!", "success")
        return redirect(url_for("products.list_products"))

    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user.id
        session["role"] = user.role
        session["name"] = user.name
        flash("Logged in successfully.", "success")
        return redirect(url_for("products.list_products"))

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("products.list_products"))
