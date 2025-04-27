from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, Div

from ufo_shop.models import Item


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
    class Meta:
        model = Item
        # Include all fields you want in the form, excluding the merchandiser
        # as it will be set automatically in the view.
        fields = ['name', 'price', 'amount', 'location', 'short_description', 'description', 'category', 'is_active']

    # Optional: Add crispy forms helper for layout customization if needed later
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.helper = FormHelper()
    #     self.helper.l
