from functools import wraps
from flask import session, redirect, url_for, abort, flash
from models import User


def current_user():
    """Fetch the logged-in user from the DB using the session cookie. No JS/tokens involved."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*allowed_roles):
    """Restricts a route to specific roles. This is the REAL enforcement point —
    templates only hide buttons for convenience, this decorator is what actually
    blocks a non-admin from reaching a restricted action."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))
            if session.get("role") not in allowed_roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
