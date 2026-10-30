# Pure Flora — Django marketplace

The original HTML/CSS frontend remains under its original names and styling. Django renders the existing home, product listing, cart, account, and florist dashboard pages; workflow pages for product details, COD checkout, order success, florist orders, and marketplace administration use the same styles. The standalone root-level `.html` prototype uses browser-local demo data; use the Django server routes for database-backed orders.

## First-time setup (Windows PowerShell)

Open the project folder in VS Code, then choose **Terminal → New Terminal**. Make sure the terminal is in the folder that contains `manage.py` (the Django project folder, not its parent folder).

Requirements: Python 3.10 or newer and an internet connection for installing Python packages and loading the sample flower images.

Create a virtual environment, install dependencies, set up the local SQLite database, load sample flowers, and start the server:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_flowers
python manage.py runserver
```

If PowerShell blocks `Activate.ps1`, allow it for this terminal only and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open **http://127.0.0.1:8000/** in your browser. Keep the terminal open while using the site; press **Ctrl+C** there to stop the server.

### Run it again later

Open a terminal in the project folder and run:

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

### Accounts and admin

Register customer and florist accounts at `/accounts/register/`. For admin access, create a local superuser:

```powershell
python manage.py createsuperuser
```

Then sign in at `/accounts/login/`. Django admin is at `/django-admin/`; the marketplace dashboard is at `/market-admin/`.

### Common startup fixes

- **`py` is not recognized:** install Python 3.10+ and enable the Python launcher / PATH option, then reopen the terminal.
- **`No module named django` or `PIL`:** activate `.venv` and run `python -m pip install -r requirements.txt` again.
- **Missing database tables:** run `python manage.py migrate` from the project folder.
- **No products appear:** run `python manage.py seed_flowers`.
- **Port 8000 is already in use:** run `python manage.py runserver 8001`, then open `http://127.0.0.1:8001/`.

The `seed_flowers` command safely imports or updates the twelve sample flower listings. New database migrations are not needed for a normal fresh setup; run `makemigrations` only after changing Django models. This configuration is for local development (`DEBUG=True`), not public production hosting.

The florist product form accepts an uploaded image or a remote image URL. Uploaded images are served from `/media/` during local development. Product listings support search, category, maximum price, stock, sorting, and pagination. Customers sign in to add products and place COD orders; florists manage listings and fulfillment in their dashboard. No online payment provider is configured.

## Main app files

- `marketplace/models.py` — users, florist profiles, categories, products, carts, orders, and delivery records
- `marketplace/forms.py` — registration, login, delivery, product, and order status forms
- `marketplace/views.py` / `marketplace/urls.py` — server-rendered workflows and role enforcement
- `marketplace/admin.py` — staff management for marketplace data
- `templates/` — Django templates copied and adapted from the supplied frontend plus the missing workflow pages
- `static/css/style.css` — original stylesheet copied unchanged

## Suggested local test accounts

Register one customer and one florist through the site. Create a superuser with `createsuperuser`; the custom user model assigns the admin role to superusers. Use distinct local-only passwords, then add categories and florist products through the Django admin or florist dashboard.

## Manual testing checklist

1. Add categories in Django admin and register a florist and a customer.
2. Sign in as florist, add a product, edit it, verify another florist cannot edit it, and review its listing.
3. Sign in as customer, browse products, add a product, update quantity within stock, remove it, and add it again.
4. Attempt checkout while signed out; sign in as customer and submit delivery details.
5. Place a COD order, verify the order number and success page, confirm inventory decreased and the cart cleared.
6. Try to exceed stock in the cart or order stale inventory and confirm the order is rejected with a message.
7. Sign in as florist, view orders containing their products, and update order status.
8. Sign in as superuser, review marketplace counts and orders at `/market-admin/`, and manage products/orders in `/django-admin/`.

No Docker, Celery, external payment provider, REST API, or CSS framework is used.
