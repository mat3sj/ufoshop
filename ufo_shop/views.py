from django.template.loader import render_to_string
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from ufo_shop.models import Item, Category
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from ufo_shop.forms import EmailAuthenticationForm, SignUpForm
from ufo_shop.utils import ufoshop_send_email


class CustomLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = 'ufo_shop/login.html'
    success_url = reverse_lazy('home')


class SignUpView(CreateView):
    model = get_user_model()
    form_class = SignUpForm  # Use the custom form
    template_name = 'ufo_shop/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        ufoshop_send_email(
            subject='Welcome to UFO Shop!',
            html_message=render_to_string('ufo_shop/email/welcome.html', {
                'user': user
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


class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'ufo_shop/home.html')


class ItemListView(ListView):
    model = Item
    template_name = 'ufo_shop/shop.html'  # Specify the template
    context_object_name = 'item_list'
    paginate_by = 12

    def get_queryset(self):
        return Item.objects.filter(is_active=True)

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
    #
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
        ).exclude(id=self.object.id)[:4]
        context['categories'] = Category.objects.all()
        return context
