# Role-Based E-Commerce Platform (Flask + MySQL)

Server-rendered marketplace with three roles: **Admin**, **Sales Person**, **User**.
**No JavaScript** — every interaction (search, filters, cart, checkout) is a plain HTML `<form>`
submission with a full page reload. Images via Cloudinary, payments via **Razorpay Payment
Links** (works with zero client-side JS: the browser is redirected to Razorpay's hosted page and
back).

## Stack
- Backend: Python, Flask, Flask-SQLAlchemy
- Database: MySQL (via PyMySQL)
- Frontend: HTML + Jinja2 templates + plain CSS (no JS, no framework)
- Auth: server-side sessions (Flask `session`, cookie-based) + Werkzeug password hashing
- Images: Cloudinary (server-side upload, only the URL is stored in MySQL)
- Payments: Razorpay Payment Links API (test mode)

## Why Payment Links instead of the usual Razorpay checkout popup
Razorpay's normal checkout is a JS widget that opens a payment modal in-page. Since this build
has no JavaScript at all, it uses Razorpay's **Payment Links API** instead: the backend creates a
payment link, and the browser is redirected (a normal HTTP redirect, same as clicking a link) to
Razorpay's own hosted payment page. After paying, Razorpay redirects back to our `/payment/callback`
route with a signature we verify server-side before marking the order paid. No popup, no JS.

## Folder structure
```
flask-ecommerce/
  app.py              # entry point, blueprint registration
  config.py            # env-based config
  models.py             # User, Product, CartItem, WishlistItem, Order, OrderItem
  extensions.py
  routes/              # auth, products, cart, wishlist, orders, payment, admin
  utils/               # auth.py (session + role_required decorator), clients.py
  templates/           # Jinja2 HTML, no JS
  static/css/style.css # plain CSS
```

## 1. Get your keys (do this first)

**MySQL**: create a local database or use a free host (PlanetScale, Railway, Aiven).
```sql
CREATE DATABASE ecommerce_db;
```

**Cloudinary** (free tier): sign up at cloudinary.com → Dashboard shows Cloud Name, API Key, API Secret.

**Razorpay** (test mode, free):
1. Sign up at razorpay.com → switch to **Test Mode**
2. Settings → API Keys → Generate Test Key → copy Key Id and Key Secret
3. Test card at checkout: `4111 1111 1111 1111`, any future expiry, any CVV, any OTP

## 2. Local setup
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# fill in DATABASE_URL, FLASK_SECRET_KEY (any random string), Cloudinary + Razorpay keys
# BASE_URL=http://localhost:5000 for local testing

python app.py       # tables are auto-created on first run; visit http://localhost:5000
```

> Razorpay needs a **public** callback URL to redirect back to. For local testing, tunnel your
> app with `ngrok http 5000` and set `BASE_URL` to the ngrok URL so the payment callback works.

## 3. Creating your first Admin
Every signup becomes a `user` by default (enforced server-side — there is no "register as admin"
option). To create your first Admin:
1. Register a normal account.
2. In MySQL, run: `UPDATE users SET role='admin' WHERE email='youremail@example.com';`
3. Log back in — you'll see the Admin link and can promote others (e.g. to `sales`) from the dashboard.

## 4. Test login credentials (fill in after creating them)

| Role         | Email               | Password  |
|--------------|----------------------|-----------|
| Admin        | admin@example.com    | ********  |
| Sales Person | sales@example.com    | ********  |
| User         | user@example.com     | ********  |

## 5. Deployment (Render only)
This app is fully server-rendered (Flask returns HTML directly) — there's no separate frontend
bundle to deploy to Vercel. Deploy the whole app to **Render** as one Web Service:
1. New Web Service → connect your GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app` (already in the `Procfile`)
4. Add all `.env` variables under Environment — including `BASE_URL` set to your live Render URL
   (e.g. `https://your-app.onrender.com`), since Razorpay needs this for the payment callback
5. Add a managed MySQL database (e.g. Render's MySQL, PlanetScale, or Railway) and point
   `DATABASE_URL` at it

After deploying: register → browse → add to cart → checkout → pay with the Razorpay test card →
confirm you land back on Orders with the order visible.

## Screenshots
(Add 2-3 screenshots here: product grid, checkout redirect, admin dashboard)

## Where role enforcement actually happens
Every restricted route uses `role_required(...)` in `utils/auth.py`, which checks the **server-side
session** (not anything the browser can fake) and returns a `403` page if the role doesn't match.
Templates only hide buttons for a cleaner UI — that's convenience, not security. A Sales Person
manually POSTing to another seller's product-delete URL gets rejected in `routes/products.py`
by the ownership check, independent of what the UI shows them.
