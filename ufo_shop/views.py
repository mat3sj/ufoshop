from django.views import View
from django.views.generic import ListView, DetailView

from django.shortcuts import render
from ufo_shop.models import Item, Category
from django.contrib.auth.models import User


class HomeView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'ufo_shop/home.html')


class ItemListView(ListView):
    model = Item
    template_name = 'ufo_shop/shop.html'  # Specify the template
    context_object_name = 'shop'
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
