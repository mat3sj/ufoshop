from django.template.loader import render_to_string
from django.views import View
# Import UpdateView
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from ufo_shop import forms
from ufo_shop.models import Item, Category
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from ufo_shop.utils import ufoshop_send_email


class CustomLoginView(LoginView):
    authentication_form = forms.EmailAuthenticationForm
    template_name = 'ufo_shop/login.html'
    success_url = reverse_lazy('home')


class SignUpView(CreateView):
    model = get_user_model()
    form_class = forms.SignUpForm  # Use the custom form
    template_name = 'ufo_shop/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object

        profile_url = self.request.build_absolute_uri(reverse_lazy('profile'))
        shop_url = self.request.build_absolute_uri(reverse_lazy('shop'))
        ufoshop_send_email(
            subject='Welcome to UFO Shop!',
            html_message=render_to_string('ufo_shop/email/welcome.html', {
                'user': user,
                'profile_url': profile_url,
                'shop_url': shop_url
            }),
            recipient_list=[user.email],
        )
        return response


class CustomLogoutView(LogoutView):
    next_page = 'home'


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ufo_shop/profile.html', {
            'user': request.user
        })

class MerchandiserSignupView(LoginRequiredMixin,View):
    # def get(self, request):
    #     user = request.user
    #     return render(request, 'ufo_shop/merchandiser_signup.html', {
    #         'user': user
    #     })
    #
    # def post(self, request):
    pass

class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'ufo_shop/home.html')


class ItemListView(ListView):
    model = Item
    template_name = 'ufo_shop/shop.html'  # Specify the template
    context_object_name = 'item_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)  # Only active items
        category = self.request.GET.get('category')
        # user = self.request.GET.get('user')

        if category:
            queryset = queryset.filter(category__id=category)
        # Merchandiser filter
        # if user:
        #     queryset = queryset.filter(merchandiser__id=user)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()  # Pass categories to the template
        # context['users'] = User.objects.filter(item__isnull=False, is_staff=True).distinct()  # Merchandisers with items
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = 'ufo_shop/item_detail.html'
    context_object_name = 'item'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['related_items'] = Item.objects.filter(
            category__in=self.object.category.all(),
            is_active=True
        ).exclude(id=self.object.id)[:6]

        context['categories'] = Category.objects.all()

        # Check if the current user can edit this item
        can_edit = False
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser or self.object.merchandiser == self.request.user:
                can_edit = True
        context['can_edit'] = can_edit
        return context


class MerchandiserShopView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'ufo_shop/merchandiser_shop.html'
    context_object_name = 'items'
    success_url = reverse_lazy('merchandiser_shop')

    def get_queryset(self):
        # Only show items belonging to the logged-in user
        return Item.objects.filter(merchandiser=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# View for creating a new item
class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = forms.ItemForm  # Use the ItemForm
    template_name = 'ufo_shop/item_form.html'
    success_url = reverse_lazy('merchandiser_shop')

    def form_valid(self, form):
        # Assign the current logged-in user as the merchandiser
        form.instance.merchandiser = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Item'
        return context


# View for updating an existing item
class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    fields = ['name', 'price', 'amount', 'location', 'short_description', 'description', 'category', 'is_active']
    template_name = 'ufo_shop/item_form.html'
    success_url = reverse_lazy('merchandiser_shop')

    def get_queryset(self):
        # Ensure users can only edit their own items
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(merchandiser=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Item' # Add title for the template
        return context