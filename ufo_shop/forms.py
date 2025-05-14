from django import forms
import os
from PIL import Image

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, Div, HTML

from ufo_shop import settings
from ufo_shop.models import Item, Order, OrderItem, Location

# Payment method choices - only QR code is allowed
PAYMENT_METHODS = [
    ('qr_code', 'QR Code Payment'),
]


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'  # Optional, for Bootstrap horizontal layout
        self.helper.label_class = 'col-sm-3'  # Bootstrap column for labels
        self.helper.field_class = 'col-sm-9'  # Bootstrap column for fields

        # Layout configuration
        self.helper.layout = Layout(
            Fieldset(
                'Login with Email',
                'username',  # The "email" field
                'password',  # AuthenticationForm's default "password" field
            ),
            Div(
                Submit('submit', 'Login', css_class='btn btn-primary'),
                css_class='text-center mt-3'
            )
        )


class SignUpForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'  # Optional for additional styling
        self.helper.label_class = 'col-sm-3'        # Bootstrap column for labels
        self.helper.field_class = 'col-sm-9'        # Bootstrap column for fields

        # Crispy Layout
        self.helper.layout = Layout(
            Fieldset(
                'Sign Up',  # Section title (optional)
                'email',
                'password1',
                'password2',
            ),
            Div(
                Submit('submit', 'Sign Up', css_class='btn btn-primary'),
                css_class='text-center mt-3'
            )
        )


class ItemForm(forms.ModelForm):
    images = forms.ImageField(
        label="Upload Images",
        widget=forms.ClearableFileInput(
            # attrs={'multiple': True}
        ),
        required=False  # Make it optional if items can be created without images initially
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'

        # Filter locations to show only those created by the user and universal ones
        if self.user:
            self.fields['locations'].queryset = Location.objects.filter(
                models.Q(merchandiser=self.user) | models.Q(is_universal=True)
            )

        self.helper.layout = Layout(
            Fieldset(
                'Item Details',
                Row(
                    Column('name', css_class='form-group col-md-6'),
                    Column('price', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('amount', css_class='form-group col-md-6'),
                    Column('locations', css_class='form-group col-md-6'),
                ),
                'short_description',
                'description',
                'category',
                'is_active',
                'images',
            ),
            Div(
                Submit('submit', 'Save Item', css_class='btn btn-primary'),
                css_class='text-center mt-3'
            )
        )
    class Meta:
        model = Item
        # List all fields EXCEPT any old image field that was directly on Item
        fields = [
            'name', 'price', 'amount', 'locations',
            'short_description', 'description', 'category', 'is_active'
            # DO NOT include 'pictures' or any single ImageField previously on Item here
        ]


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'})
    )
    item_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Row(
                Column('quantity', css_class='form-group col-auto'),
                Column('item_id', css_class='form-group d-none'),
                Column(
                    Submit('submit', 'Add to Cart', css_class='btn btn-success'),
                    css_class='form-group col-auto'
                ),
                css_class='align-items-center'
            )
        )


class CartUpdateForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px;'})
    )
    item_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Row(
                Column('quantity', css_class='form-group col-auto'),
                Column('item_id', css_class='form-group d-none'),
                Column(
                    Submit('update', 'Update', css_class='btn btn-sm btn-outline-secondary'),
                    css_class='form-group col-auto'
                ),
                css_class='align-items-center'
            )
        )


class CheckoutForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(),
        required=True,
        initial='qr_code'  # Default to QR code since it's the only option
    )

    needs_receipt = forms.BooleanField(
        label="I need a receipt (+7% fee)",
        required=False,
        help_text="Check this box if you need a receipt. A 7% fee will be added to your order."
    )

    def __init__(self, *args, **kwargs):
        self.cart_items = kwargs.pop('cart_items', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'

        # Create dynamic fields for pickup locations
        self.pickup_location_fields = {}
        if self.cart_items:
            for item in self.cart_items:
                field_name = f'pickup_location_{item.id}'
                # Get available locations for this item
                locations = item.item.locations.all()
                if not locations.exists():
                    # If no locations are set, use all universal locations
                    locations = Location.objects.filter(is_universal=True)

                self.fields[field_name] = forms.ModelChoiceField(
                    queryset=locations,
                    label=f'Pickup Location for {item.item.name}',
                    required=True,
                    empty_label="Select a pickup location"
                )
                self.pickup_location_fields[item.id] = field_name

        # Build the form layout
        pickup_locations_fieldset = None
        if self.pickup_location_fields:
            pickup_fields = []
            for field_name in self.pickup_location_fields.values():
                pickup_fields.append(field_name)

            pickup_locations_fieldset = Fieldset(
                'Pickup Locations',
                *pickup_fields
            )

        layout_elements = [
            Fieldset(
                'Contact Information',
                Row(
                    Column('contact_email', css_class='form-group col-md-6'),
                    Column('contact_phone', css_class='form-group col-md-6'),
                ),
            ),
        ]

        if pickup_locations_fieldset:
            layout_elements.append(pickup_locations_fieldset)

        layout_elements.extend([
            Fieldset(
                'Payment Method',
                'payment_method',
                'needs_receipt',
            ),
            Div(
                Submit('submit', 'Complete Order', css_class='btn btn-success btn-lg'),
                css_class='text-center mt-4'
            )
        ])

        self.helper.layout = Layout(*layout_elements)

    def get_pickup_location(self, item_id):
        field_name = self.pickup_location_fields.get(item_id)
        if field_name and field_name in self.cleaned_data:
            return self.cleaned_data[field_name]
        return None

    class Meta:
        model = Order
        fields = [
            'contact_email', 'contact_phone', 'payment_method', 'needs_receipt'
        ]
