"""
URL configuration for ufo_shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns

from ufo_shop import views

urlpatterns = [
    # Language selection
    path('i18n/', include('django.conf.urls.i18n')),

    # Admin route
    path('admin/', admin.site.urls, name='admin'),

    # Home page
    path('', views.HomeView.as_view(), name='home'),

    # Shop page
    path('shop/', views.ItemListView.as_view(), name='shop'),
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('merchandiser_shop/', views.MerchandiserShopView.as_view(), name='merchandiser_shop'),

    # Items CRUD for Merchandisers
    path('item/create/', views.ItemCreateView.as_view(), name='item-create'), # New URL for creating items
    path('item/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item-edit'),   # New URL for editing items

    # Cart and Checkout
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/update/', views.UpdateCartView.as_view(), name='update_cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('order/<int:pk>/confirmation/', views.OrderConfirmationView.as_view(), name='order_confirmation'),
    path('orders/', views.OrderHistoryView.as_view(), name='orders'),

    # # About page
    # path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    #
    # User-related pages (to be implemented in views)
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/signup/', views.SignUpView.as_view(), name='signup'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/merchandiser_signup/', views.MerchandiserSignupView.as_view(), name='merchandiser_signup'),
    #
    # # Privacy policy and terms of service
    # path('privacy-policy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    # path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
