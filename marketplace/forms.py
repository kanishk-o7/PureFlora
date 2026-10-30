"""Server-side forms used by customer and florist workflows."""
import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from decimal import Decimal
from .models import CustomUser, DeliveryInfo, Product, OrderItem, FloristProfile, Review, CustomerAddress

class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    role = forms.ChoiceField(choices=[("customer", "Customer"), ("florist", "Florist / Seller")])
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role")

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autocomplete": "username"}))

class DeliveryForm(forms.ModelForm):
    class Meta:
        model = DeliveryInfo
        fields = ("full_name", "phone", "address", "city", "state", "pin_code")
        help_texts = {"phone": "Enter a 10-digit mobile number. You may include the +91 country code."}
        widgets = {
            "phone": forms.TextInput(attrs={
                "type": "tel",
                "inputmode": "tel",
                "autocomplete": "tel",
                "placeholder": "+91 98765 43210",
            }),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_phone(self):
        raw_phone = self.cleaned_data["phone"].strip()
        if not re.fullmatch(r"[0-9+()\s-]+", raw_phone):
            raise forms.ValidationError("Enter a valid mobile number.")

        normalized = re.sub(r"[\s()-]", "", raw_phone)
        if normalized.startswith("+91"):
            normalized = normalized[3:]
        elif normalized.startswith("91") and len(normalized) == 12:
            normalized = normalized[2:]

        if not re.fullmatch(r"[6-9][0-9]{9}", normalized):
            raise forms.ValidationError(
                "Enter a valid 10-digit mobile number."
            )
        return normalized

class CustomerAddressForm(forms.ModelForm):
    class Meta:
        model = CustomerAddress
        fields = ("recipient_name", "phone_number", "street_address", "city", "state", "pincode", "landmark", "is_default")
        widgets = {
            "phone_number": forms.TextInput(attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel", "placeholder": "+91 98765 43210"}),
            "street_address": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_phone_number(self):
        raw_phone = self.cleaned_data["phone_number"].strip()
        if not re.fullmatch(r"[0-9+()\s-]+", raw_phone):
            raise forms.ValidationError("Enter a valid mobile number.")
        normalized = re.sub(r"[\s()-]", "", raw_phone)
        if normalized.startswith("+91"):
            normalized = normalized[3:]
        elif normalized.startswith("91") and len(normalized) == 12:
            normalized = normalized[2:]
        if not re.fullmatch(r"[6-9][0-9]{9}", normalized):
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return normalized

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "price", "unit", "image", "image_url", "stock", "is_active")

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= Decimal("0.00"):
            raise forms.ValidationError("Price must be greater than zero.")
        return price

class FloristProfileForm(forms.ModelForm):
    class Meta:
        model = FloristProfile
        fields = ("shop_name", "bio", "phone_number", "address", "profile_image")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4}), "address": forms.Textarea(attrs={"rows": 3})}

class OrderItemStatusForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ("fulfillment_status",)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(attrs={"class": "review-rating"}),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Share a few details about your flowers (optional)."}),
        }
