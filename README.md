# Pure Flora — Django marketplace

The original HTML/CSS frontend remains under its original names and styling. Django renders the existing home, product listing, cart, account, and florist dashboard pages; workflow pages for product details, COD checkout, order success, florist orders, and marketplace administration use the same styles.

## Run locally

From this directory, activate the project virtual environment and run:

```powershell
python -m pip install -r requirements.txt
python manage.py makemigrations marketplace
python manage.py migrate
python manage.py seed_flowers
python manage.py createsuperuser
python manage.py runserver
```

The florist product form accepts either an uploaded image or a remote image URL. Uploaded images are served from `/media/` during local development; remote image URLs from the original seed catalog remain as fallback. Product listings support search, category, maximum price, stock, sorting, and pagination.

Open `http://127.0.0.1:8000/`. The Django admin is at `/django-admin/`, and the marketplace admin overview is at `/market-admin/` for a superuser.

The `seed_flowers` command imports the twelve flower listings from the original frontend demo and can be run again safely. Then register customer and florist accounts through `/accounts/register/`. Florists can create additional listings from the florist dashboard. Customers must sign in to add items and place orders. Checkout uses Cash on Delivery only.

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
