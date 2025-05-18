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
        widget=forms.FileInput(),
        required=False  # Make it optional if items can be created without images initially
    )

    # Fields for color variants
    has_color_variants = forms.BooleanField(
        label="This item has color variants",
        required=False,
        initial=False,
        help_text="Check this if you want to add color variants for this item"
    )

    # For creating a new variant of an existing item
    is_variant_of = forms.ModelChoiceField(
        queryset=Item.objects.filter(is_variant=False),
        label="This is a color variant of",
        required=False,
        help_text="Select the parent item if this is a color variant"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'
        self.helper.attrs = {'enctype': 'multipart/form-data'}
        self.helper.form_tag = False

        # Filter locations to show only those created by the user and universal ones
        if self.user:
            self.fields['locations'].queryset = Location.objects.filter(
                models.Q(merchandiser=self.user) | models.Q(is_universal=True)
            )

            # Filter is_variant_of to show only items belonging to the user
            self.fields['is_variant_of'].queryset = Item.objects.filter(
                merchandiser=self.user,
                is_variant=False
            )

        # If this is an existing item that is a variant, hide the has_color_variants field
        if self.instance and self.instance.pk and self.instance.is_variant:
            self.fields['has_color_variants'].widget = forms.HiddenInput()
            self.fields['has_color_variants'].initial = False

        # If this is an existing item with variants, set has_color_variants to True
        if self.instance and self.instance.pk and self.instance.has_variants():
            self.fields['has_color_variants'].initial = True

        # If this is an existing variant, set is_variant_of to the parent item
        if self.instance and self.instance.pk and self.instance.is_variant and self.instance.parent_item:
            self.fields['is_variant_of'].initial = self.instance.parent_item

        # Build the layout based on whether this is a variant or not
        color_fields = []
        if self.instance and self.instance.pk and self.instance.is_variant:
            # This is an existing variant, show color field
            color_fields = [
                Row(
                    Column('color', css_class='form-group col-md-6'),
                    Column('is_variant_of', css_class='form-group col-md-6'),
                ),
            ]
        else:
            # This is a new item or an existing non-variant item
            color_fields = [
                Row(
                    Column('has_color_variants', css_class='form-group col-md-6'),
                    Column('color', css_class='form-group col-md-6', css_id='color_field'),
                ),
                Row(
                    Column('is_variant_of', css_class='form-group col-md-12'),
                ),
            ]

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
                *color_fields,
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

    def clean(self):
        cleaned_data = super().clean()
        is_variant_of = cleaned_data.get('is_variant_of')
        color = cleaned_data.get('color')

        # If this is a variant, color is required
        if is_variant_of and not color:
            self.add_error('color', 'Color is required for variants')

        return cleaned_data

    class Meta:
        model = Item
        # List all fields EXCEPT any old image field that was directly on Item
        fields = [
            'name', 'price', 'amount', 'locations',
            'short_description', 'description', 'category', 'is_active',
            'color'  # Add color field
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
