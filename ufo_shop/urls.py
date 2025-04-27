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
from django.contrib import admin
from django.urls import path

from ufo_shop import views

urlpatterns = [
    # Admin route
    path('admin/', admin.site.urls, name='admin'),

    # Home page
    path('', views.HomeView.as_view(), name='home'),

    # Shop page
    path('shop/', views.ItemListView.as_view(), name='shop'),
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),

    # # About page
    # path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    #
    # User-related pages (to be implemented in views)
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('merchandiser_shop/', views.MerchandiserShopView.as_view(), name='merchandiser_shop'),
    path('merchandiser_signup/', views.MerchandiserSignupView.as_view(), name='merchandiser_signup'),
    #
    # # User profile/orders page
    # path('orders/', TemplateView.as_view(template_name='orders.html'), name='orders'),
    #
    # # Privacy policy and terms of service
    # path('privacy-policy/', TemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    # path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
]
