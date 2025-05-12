from django import forms
import os
from PIL import Image

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, Div, HTML

from ufo_shop import settings
from ufo_shop.models import Item, Order, OrderItem

# Payment method choices
PAYMENT_METHODS = [
    ('credit_card', 'Credit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('paypal', 'PayPal'),
    ('cash_on_delivery', 'Cash on Delivery'),
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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-sm-3'
        self.helper.field_class = 'col-sm-9'

        self.helper.layout = Layout(
            Fieldset(
                'Item Details',
                Row(
                    Column('name', css_class='form-group col-md-6'),
                    Column('price', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('amount', css_class='form-group col-md-6'),
                    Column('location', css_class='form-group col-md-6'),
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
            'name', 'price', 'amount', 'location',
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
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'

        self.helper.layout = Layout(
            Fieldset(
                'Shipping Information',
                Row(
                    Column('shipping_address', css_class='form-group col-md-12'),
                ),
                Row(
                    Column('shipping_city', css_class='form-group col-md-6'),
                    Column('shipping_state', css_class='form-group col-md-6'),
                ),
                Row(
                    Column('shipping_country', css_class='form-group col-md-6'),
                    Column('shipping_zip', css_class='form-group col-md-6'),
                ),
            ),
            Fieldset(
                'Contact Information',
                Row(
                    Column('contact_email', css_class='form-group col-md-6'),
                    Column('contact_phone', css_class='form-group col-md-6'),
                ),
            ),
            Fieldset(
                'Payment Method',
                'payment_method',
            ),
            Div(
                Submit('submit', 'Complete Order', css_class='btn btn-success btn-lg'),
                css_class='text-center mt-4'
            )
        )

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'shipping_zip', 'contact_email', 
            'contact_phone', 'payment_method'
        ]
