"""Server-rendered marketplace workflows with role checks and stock-safe checkout."""
from decimal import Decimal
from functools import wraps
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum, F
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, LoginForm, DeliveryForm, ProductForm, OrderItemStatusForm, FloristProfileForm
from .models import CustomUser, Category, Product, Cart, CartItem, Order, OrderItem, DeliveryInfo, FloristProfile

def access_denied(request):
    """Render the themed forbidden page for authenticated users without access."""
    return render(request, "403.html", status=403)

def handler403(request, exception=None):
    return render(request, "403.html", status=403)

def handler404(request, exception=None):
    return render(request, "404.html", status=404)

def handler500(request):
    return render(request, "500.html", status=500)

def role_required(*roles):
    """Require a signed-in user with one of the listed marketplace roles."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, "Please sign in to continue.")
                return redirect("login")
            if request.user.role not in roles and not request.user.is_superuser:
                return access_denied(request)
            return view(request, *args, **kwargs)
        return wrapped
    return decorator

def home(request):
    return render(request, "index.html", {"featured_products": Product.objects.filter(is_active=True, stock__gt=0).select_related("category", "florist")[:4]})

def products(request):
    items = Product.objects.filter(is_active=True).select_related("category", "florist")
    category = request.GET.get("category", "")
    search = request.GET.get("q", "")
    max_price = request.GET.get("max_price", "1000")
    in_stock = request.GET.get("in_stock", "") == "1"
    sort = request.GET.get("sort", "featured")
    if category and category.lower() != "all": items = items.filter(category__name__iexact=category)
    if search: items = items.filter(Q(name__icontains=search) | Q(description__icontains=search) | Q(florist__username__icontains=search))
    try:
        price_limit = Decimal(max_price)
        if price_limit >= 0:
            items = items.filter(price__lte=price_limit)
    except (ArithmeticError, ValueError):
        max_price = "1000"
    if in_stock:
        items = items.filter(stock__gt=0)
    ordering = {"price-asc": "price", "price-desc": "-price", "name": "name"}.get(sort, "-created_at")
    items = items.order_by(ordering, "pk")
    result_count = items.count()
    page_obj = Paginator(items, 12).get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    cart_count = 0
    if request.user.is_authenticated and request.user.role == "customer":
        cart_count = sum(_get_cart(request.user).items.values_list("quantity", flat=True))
    try:
        added_product_id = int(request.GET.get("added", ""))
    except (TypeError, ValueError):
        added_product_id = None
    return render(request, "products.html", {
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "result_count": result_count,
        "query_string": query_params.urlencode(),
        "categories": Category.objects.all(),
        "selected_category": category,
        "search_query": search,
        "max_price": max_price,
        "in_stock": in_stock,
        "sort": sort,
        "cart_count": cart_count,
        "added_product_id": added_product_id,
    })

def product_detail(request, pk):
    return render(request, "product_detail.html", {"product": get_object_or_404(Product, pk=pk, is_active=True)})

def _get_cart(user):
    return Cart.objects.get_or_create(customer=user)[0]

def cart_view(request):
    items = []
    total = Decimal("0.00")
    count = 0
    if request.user.is_authenticated and request.user.role == "customer":
        items = _get_cart(request.user).items.select_related("product", "product__category").all()
        total = sum((item.line_total for item in items), Decimal("0.00"))
        count = sum(item.quantity for item in items)
    return render(request, "cart.html", {"cart_items": items, "subtotal": total, "item_count": count})

@require_POST
@role_required("customer")
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    if product.stock <= 0:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "This flower is sold out."}, status=400)
        messages.error(request, "Insufficient stock: this flower is sold out.")
        return redirect("products")
    cart = _get_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 1})
    if not created:
        if item.quantity >= product.stock:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "message": "You have added all available stock."}, status=400)
            messages.error(request, "Insufficient stock for the requested quantity.")
            return redirect("cart")
        item.quantity += 1
        item.save(update_fields=["quantity"])
    messages.success(request, "Added to cart.")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        count = sum(cart.items.values_list("quantity", flat=True))
        return JsonResponse({"ok": True, "message": "Added to cart.", "cart_count": count})
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        # Return to the same catalog/filter state and anchor on the flower just added.
        parts = urlsplit(next_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["added"] = str(product.pk)
        return redirect(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), f"product-{product.pk}")))
    return redirect("cart")

@require_POST
@role_required("customer")
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__customer=request.user)
    try: quantity = int(request.POST.get("quantity", "1"))
    except ValueError: quantity = 0
    if quantity < 1:
        messages.error(request, "Quantity must be at least one.")
    elif quantity > item.product.stock:
        messages.error(request, "Insufficient stock for that quantity.")
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        messages.success(request, "Cart quantity updated.")
    return redirect("cart")

@require_POST
@role_required("customer")
def remove_cart_item(request, item_id):
    get_object_or_404(CartItem, pk=item_id, cart__customer=request.user).delete()
    return redirect("cart")

@role_required("customer")
def checkout(request):
    cart = _get_cart(request.user)
    items = list(cart.items.select_related("product").all())
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("products")
    form = DeliveryForm(request.POST or None, initial={"full_name": request.user.get_full_name()})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                # Re-read and lock current inventory just before the COD order is committed.
                locked_items = list(cart.items.select_related("product").select_for_update())
                total = Decimal("0.00")
                for item in locked_items:
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    if not product.is_active or product.stock < item.quantity:
                        raise ValueError(f"Insufficient stock for {product.name}; please update your cart.")
                    total += product.price * item.quantity
                order = Order.objects.create(customer=request.user, total_amount=total, payment_method="COD")
                for item in locked_items:
                    product = Product.objects.select_for_update().get(pk=item.product_id)
                    OrderItem.objects.create(order=order, product=product, florist=product.florist, product_name=product.name, unit_price=product.price, quantity=item.quantity)
                    product.stock -= item.quantity
                    product.save(update_fields=["stock"])
                delivery = form.save(commit=False)
                delivery.order = order
                delivery.save()
                cart.items.all().delete()
        except ValueError as error:
            messages.error(request, str(error))
            return redirect("cart")
        messages.success(request, "Order placed successfully. Pay cash on delivery.")
        return redirect("order_success", order_number=order.order_number)
    return render(request, "checkout.html", {"form": form, "cart_items": items, "total": sum((i.line_total for i in items), Decimal("0.00"))})

@role_required("customer", "admin")
def order_success(request, order_number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), order_number=order_number)
    if not (request.user.is_superuser or request.user.role == "admin" or order.customer_id == request.user.id):
        return access_denied(request)
    return render(request, "order_success.html", {"order": order})

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        if user.role == "florist": FloristProfile.objects.create(user=user, shop_name=user.get_full_name())
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("florist_dashboard" if user.role == "florist" else "home")
    return render(request, "auth.html", {"register_form": form, "login_form": LoginForm(), "mode": "register"})

def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        user = form.get_user()
        return redirect("admin_dashboard" if user.role == "admin" or user.is_superuser else "florist_dashboard" if user.role == "florist" else "home")
    if request.method == "POST": messages.error(request, "Please check your username and password.")
    return render(request, "auth.html", {"login_form": form, "register_form": RegistrationForm(), "mode": "login"})

def logout_view(request):
    logout(request)
    messages.info(request, "You have signed out.")
    return redirect("home")

@role_required("florist")
def florist_dashboard(request):
    products = Product.objects.filter(florist=request.user).select_related("category")
    orders = Order.objects.filter(items__florist=request.user).distinct().order_by("-created_at")[:8]
    return render(request, "dashboard.html", {"seller_products": products, "seller_orders": orders, "listing_count": products.count()})

@role_required("florist")
def florist_profile(request):
    """Create or update only the signed-in florist's shop profile."""
    profile, _ = FloristProfile.objects.get_or_create(
        user=request.user, defaults={"shop_name": request.user.get_full_name()}
    )
    form = FloristProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your shop profile was updated.")
        return redirect("florist_profile")
    return render(request, "marketplace/florist_profile.html", {"form": form, "profile": profile})

@role_required("florist")
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False); product.florist = request.user; product.save()
        messages.success(request, "Product added.")
        return redirect("florist_dashboard")
    return render(request, "product_form.html", {"form": form, "title": "Add a flower listing"})

@role_required("florist")
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, florist=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Product updated."); return redirect("florist_dashboard")
    return render(request, "product_form.html", {"form": form, "title": "Edit flower listing"})

@require_POST
@role_required("florist")
def product_delete(request, pk):
    # Keep past order references intact while removing the listing from the marketplace.
    product = get_object_or_404(Product, pk=pk, florist=request.user)
    product.is_active = False
    product.save(update_fields=["is_active"])
    messages.success(request, "Product removed from the marketplace.")
    return redirect("florist_dashboard")

@role_required("florist")
def florist_orders(request):
    # Each displayed row is a vendor-owned line item, never the entire shared order.
    fulfillment_items = OrderItem.objects.filter(florist=request.user).select_related(
        "order", "order__customer", "product"
    ).order_by("-order__created_at", "pk")
    return render(request, "florist_orders.html", {"fulfillment_items": fulfillment_items})

@require_POST
@role_required("florist")
def florist_order_status(request, item_id):
    # Lock the vendor line and product together so cancellation can only restore stock once.
    with transaction.atomic():
        item = get_object_or_404(
            OrderItem.objects.select_for_update().select_related("order").filter(florist=request.user),
            pk=item_id,
        )
        previous_status = item.fulfillment_status
        form = OrderItemStatusForm(request.POST, instance=item)
        if not form.is_valid():
            messages.error(request, "Choose a valid fulfillment status.")
            return redirect("florist_orders")

        new_status = form.cleaned_data["fulfillment_status"]
        # ModelForm validation copies the submitted status onto its instance, so use
        # the database value captured before validation for transition checks.
        if previous_status == "cancelled":
            if new_status != "cancelled":
                messages.error(request, "A cancelled line item cannot be reopened.")
                return redirect("florist_orders")
            messages.info(request, "This line item is already cancelled.")
            return redirect("florist_orders")

        if new_status == "cancelled" and not item.stock_restored:
            # The conditional claim complements select_for_update on SQLite, where row-level
            # select_for_update locks are not enforced, and makes retries idempotent.
            claimed = OrderItem.objects.filter(pk=item.pk, stock_restored=False).update(stock_restored=True)
            if claimed:
                product = Product.objects.select_for_update().get(pk=item.product_id)
                product.stock = F("stock") + item.quantity
                product.save(update_fields=["stock"])
            item.stock_restored = True

        item.fulfillment_status = new_status
        item.save(update_fields=["fulfillment_status", "stock_restored"])
        item.order.sync_fulfillment()
    messages.success(request, "Your fulfillment status was updated.")
    return redirect("florist_orders")

@login_required
def order_history(request):
    """Show only the signed-in customer's own orders."""
    if request.user.role != "customer":
        return access_denied(request)
    orders = Order.objects.filter(customer=request.user).prefetch_related("items").order_by("-created_at")
    return render(request, "marketplace/order_history.html", {"orders": orders})

@login_required
def order_detail(request, order_id):
    """Fetch an order by both its ID and owner to prevent cross-customer access."""
    if request.user.role != "customer":
        return access_denied(request)
    order = get_object_or_404(
        Order.objects.filter(customer=request.user).prefetch_related("items__florist"), pk=order_id
    )
    return render(request, "marketplace/order_detail.html", {"order": order})

@role_required("admin")
def admin_dashboard(request):
    context = {"orders": Order.objects.select_related("customer").order_by("-created_at")[:20], "products": Product.objects.select_related("florist", "category"),
               "florists": CustomUser.objects.filter(role="florist"), "customers": CustomUser.objects.filter(role="customer"),
               "order_count": Order.objects.count(), "sales_total": Order.objects.exclude(order_status="cancelled").aggregate(total=Sum("total_amount"))["total"] or 0}
    return render(request, "admin_dashboard.html", context)

def tracking(request):
    """Let signed-in customers look up their own orders by order number."""
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to track your orders.")
        return redirect("login")
    order_number = request.GET.get("order_number", "").strip()
    order = None
    if order_number:
        lookup = Order.objects.prefetch_related("items").select_related("delivery_info")
        if request.user.is_superuser or request.user.role == "admin":
            order = lookup.filter(order_number__iexact=order_number).first()
        else:
            order = lookup.filter(order_number__iexact=order_number, customer=request.user).first()
        if order is None:
            messages.error(request, "We couldn't find that order in your account.")
    step_for_status = {"pending": 0, "confirmed": 1, "shipped": 3, "delivered": 4}
    current_step = step_for_status.get(order.order_status, -1) if order else -1
    if order and order.order_status == "partially_fulfilled":
        line_statuses = set(order.items.values_list("fulfillment_status", flat=True))
        current_step = 3 if line_statuses.intersection({"shipped", "delivered"}) else 1 if "processing" in line_statuses else 0
    tracking_steps = [
        {"title": "Order received", "description": "Your order has been received and is awaiting confirmation."},
        {"title": "Grower is preparing your flowers", "description": "Fresh stems are being selected and carefully packed."},
        {"title": "Ready for dispatch", "description": "Your flowers are ready to begin their journey."},
        {"title": "Out for delivery", "description": "Your order is on its way to your delivery address."},
        {"title": "Delivered with care", "description": "Your flowers have arrived."},
    ]
    return render(request, "tracking.html", {"order": order, "order_number": order_number,
                                                "current_step": current_step, "tracking_steps": tracking_steps})

def wishlist(request):
    """Render the visitor's session-backed wishlist using the existing frontend layout."""
    ids = request.session.get("wishlist", [])
    products = Product.objects.filter(pk__in=ids, is_active=True).select_related("category", "florist")
    return render(request, "wishlist.html", {"wishlist_products": products})

@require_POST
def wishlist_toggle(request, product_id):
    """Add or remove one active product from the current browser session's wishlist."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    ids = request.session.get("wishlist", [])
    product_key = str(product.pk)
    if product_key in ids:
        ids.remove(product_key)
        messages.success(request, "Removed from your favourites.")
    else:
        ids.append(product_key)
        messages.success(request, "Saved to your favourites.")
    request.session["wishlist"] = ids
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("wishlist")

def analytics(request):
    """Summarize live marketplace orders while retaining the existing insights layout."""
    month_rows = list(Order.objects.exclude(order_status="cancelled").annotate(month=TruncMonth("created_at")).values("month").annotate(total=Sum("total_amount")).order_by("-month")[:6])
    month_rows.reverse()
    maximum = max((float(row["total"] or 0) for row in month_rows), default=0) or 1
    monthly_sales = [{"label": row["month"].strftime("%b"), "height": max(4, int(float(row["total"] or 0) / maximum * 100)), "total": row["total"] or 0} for row in month_rows]
    if not monthly_sales:
        monthly_sales = [{"label": "â€”", "height": 4, "total": 0}]
    category_rows = list(Category.objects.annotate(sold=Sum("products__order_items__quantity")).order_by("-sold", "name")[:4])
    total_sold = sum((category.sold or 0) for category in category_rows) or 1
    categories = [{"name": category.name, "percentage": int((category.sold or 0) / total_sold * 100), "quantity": category.sold or 0} for category in category_rows]
    total_sales = Order.objects.exclude(order_status="cancelled").aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    order_count = Order.objects.count()
    context = {"sales_total": total_sales, "order_count": order_count,
               "active_florists": CustomUser.objects.filter(role="florist", is_active=True).count(),
               "average_order": total_sales / order_count if order_count else Decimal("0.00"),
               "monthly_sales": monthly_sales, "category_stats": categories}
    return render(request, "analytics.html", context)

