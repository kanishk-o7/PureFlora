"""Server-side forms used by customer and florist workflows."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser, DeliveryInfo, Product, OrderItem, FloristProfile

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
        fields = ("full_name", "phone", "address", "city", "pin_code")
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "name", "description", "price", "unit", "image", "image_url", "stock", "is_active")

class FloristProfileForm(forms.ModelForm):
    class Meta:
        model = FloristProfile
        fields = ("shop_name", "bio", "phone_number", "address", "profile_image")
        widgets = {"bio": forms.Textarea(attrs={"rows": 4}), "address": forms.Textarea(attrs={"rows": 3})}

class OrderItemStatusForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ("fulfillment_status",)
