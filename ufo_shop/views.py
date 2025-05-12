from django.template.loader import render_to_string
from django.views import View
# Import UpdateView
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect

from ufo_shop import forms
from ufo_shop.models import Item, Category, Picture, Order, OrderItem
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy, reverse
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

        # Add to cart form
        add_to_cart_form = forms.AddToCartForm(initial={'item_id': self.object.id})
        context['add_to_cart_form'] = add_to_cart_form

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
        # Save the Item instance
        self.object = form.save()

        # Handle multiple image uploads
        images = self.request.FILES.getlist('images') # 'images' is the name of the form field
        for image_file in images:
            Picture.objects.create(item=self.object, picture=image_file)
            # The Picture model's save() method will handle thumbnails/squares

        # Use the success_url defined on the class
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

    def form_valid(self, form):
        # Save the updated Item instance
        self.object = form.save()

        # Handle *new* multiple image uploads
        images = self.request.FILES.getlist('images') # 'images' is the name of the form field
        for image_file in images:
            Picture.objects.create(item=self.object, picture=image_file)
            # The Picture model's save() method will handle thumbnails/squares

        # Use the success_url defined on the class
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Item'
        # You might want to pass existing pictures to the template for display/management
        context['existing_pictures'] = self.object.pictures.all()
        return context


# Cart and Checkout Views
class CartView(LoginRequiredMixin, View):
    """View to display the current cart"""

    def get(self, request):
        # Get or create an order with status IN_CART for the current user
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status=Order.Status.IN_CART
        )

        # Get all items in the cart
        cart_items = cart.orderitem_set.all().select_related('item')

        # Create forms for updating quantities
        update_forms = []
        for cart_item in cart_items:
            form = forms.CartUpdateForm(initial={
                'quantity': cart_item.amount,
                'item_id': cart_item.item.id
            })
            update_forms.append((cart_item, form))

        # Calculate totals
        cart.calculate_totals()
        cart.save()

        return render(request, 'ufo_shop/cart.html', {
            'cart': cart,
            'cart_items': update_forms,
        })


class AddToCartView(LoginRequiredMixin, FormView):
    """View to add an item to the cart"""
    form_class = forms.AddToCartForm

    def form_valid(self, form):
        item_id = form.cleaned_data['item_id']
        quantity = form.cleaned_data['quantity']

        # Get the item
        item = get_object_or_404(Item, id=item_id)

        # Get or create an order with status IN_CART for the current user
        cart, created = Order.objects.get_or_create(
            user=self.request.user,
            status=Order.Status.IN_CART
        )

        # Check if the item is already in the cart
        order_item, created = OrderItem.objects.get_or_create(
            order=cart,
            item=item,
            defaults={'amount': quantity}
        )

        # If the item is already in the cart, update the quantity
        if not created:
            order_item.amount += quantity
            order_item.save()

        messages.success(self.request, f'{item.name} added to your cart.')

        # Redirect to the referring page or the cart
        next_url = self.request.POST.get('next', reverse('cart'))
        return HttpResponseRedirect(next_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Error adding item to cart. Please try again.')
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER', reverse('shop')))


class UpdateCartView(LoginRequiredMixin, FormView):
    """View to update item quantities in the cart"""
    form_class = forms.CartUpdateForm

    def form_valid(self, form):
        item_id = form.cleaned_data['item_id']
        quantity = form.cleaned_data['quantity']

        # Get the cart
        cart = get_object_or_404(Order, user=self.request.user, status=Order.Status.IN_CART)

        # Get the order item
        order_item = get_object_or_404(OrderItem, order=cart, item_id=item_id)

        # Update the quantity or remove if quantity is 0
        if quantity > 0:
            order_item.amount = quantity
            order_item.save()
            messages.success(self.request, 'Cart updated.')
        else:
            order_item.delete()
            messages.success(self.request, 'Item removed from cart.')

        # Recalculate totals
        cart.calculate_totals()
        cart.save()

        return redirect('cart')

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating cart. Please try again.')
        return redirect('cart')


class CheckoutView(LoginRequiredMixin, FormView):
    """View to collect shipping and payment information"""
    form_class = forms.CheckoutForm
    template_name = 'ufo_shop/checkout.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the cart is empty
        cart = self.get_cart()
        if not cart or cart.orderitem_set.count() == 0:
            messages.warning(request, 'Your cart is empty. Please add items before checkout.')
            return redirect('shop')
        return super().dispatch(request, *args, **kwargs)

    def get_cart(self):
        try:
            return Order.objects.get(user=self.request.user, status=Order.Status.IN_CART)
        except Order.DoesNotExist:
            return None

    def get_initial(self):
        # Pre-fill the form with user information
        user = self.request.user
        return {
            'contact_email': user.email,
            'contact_phone': user.phone,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_cart()
        cart.calculate_totals()
        context['cart'] = cart
        context['cart_items'] = cart.orderitem_set.all().select_related('item')
        return context

    def form_valid(self, form):
        cart = self.get_cart()

        # Update the cart with shipping and payment information
        for field in form.cleaned_data:
            setattr(cart, field, form.cleaned_data[field])

        # Update the status to ORDERED
        cart.status = Order.Status.ORDERED
        cart.calculate_totals()
        cart.save()

        # Send order confirmation email
        self.send_order_confirmation(cart)

        # Redirect to order confirmation page
        return redirect('order_confirmation', pk=cart.id)

    def send_order_confirmation(self, order):
        """Send order confirmation email"""
        items = order.orderitem_set.all().select_related('item')

        # Build the order URL
        order_url = self.request.build_absolute_uri(
            reverse('order_confirmation', kwargs={'pk': order.id})
        )

        # Create context for email template
        context = {
            'order': order,
            'items': items,
            'user': self.request.user,
            'order_url': order_url,
        }

        ufoshop_send_email(
            recipient_list=[order.contact_email],
            subject='Your Order Confirmation',
            html_message=render_to_string('ufo_shop/email/order_confirmation.html', context),
            plain_message=render_to_string('ufo_shop/email/order_confirmation.txt', context),
        )


class OrderConfirmationView(LoginRequiredMixin, DetailView):
    """View to display order confirmation after checkout"""
    model = Order
    template_name = 'ufo_shop/order_confirmation.html'
    context_object_name = 'order'

    def get_queryset(self):
        # Ensure users can only view their own orders
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.orderitem_set.all().select_related('item')
        return context


class OrderHistoryView(LoginRequiredMixin, ListView):
    """View to display order history"""
    model = Order
    template_name = 'ufo_shop/order_history.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Only show orders that are not in cart
        return Order.objects.filter(
            user=self.request.user
        ).exclude(
            status=Order.Status.IN_CART
        ).order_by('-created_at')
