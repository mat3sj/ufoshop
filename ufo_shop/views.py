from django.views import View
from django.views.generic import ListView, DetailView

from django.shortcuts import render
from ufo_shop.models import Item, Category
from django.contrib.auth.views import LoginView
from .forms import EmailAuthenticationForm


class MyLoginView(LoginView):
    authentication_form = EmailAuthenticationForm



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
