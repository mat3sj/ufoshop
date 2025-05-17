from django.template.loader import render_to_string
from django.views import View
# Import UpdateView
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.db.models import Count, Sum, F, Q
from ufo_shop.models import News
from django.db.models.functions import TruncMonth, TruncDay

from ufo_shop import forms
from ufo_shop.models import Item, Category, Picture, Order, OrderItem, BANK_ACCOUNT
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
        # Get top selling items
        # We'll use OrderItem to find the most sold items
        top_items = Item.objects.filter(is_active=True).annotate(
            total_sold=Count('orderitem')
        ).order_by('-total_sold')[:6]  # Get top 6 items

        # Get latest news
        latest_news = News.objects.filter(is_active=True).order_by('-published_at')[:5]  # Get latest 5 news items

        return render(request, 'ufo_shop/home.html', {
            'top_items': top_items,
            'latest_news': latest_news,
        })


class ItemListView(ListView):
    model = Item
    template_name = 'ufo_shop/shop.html'  # Specify the template
    context_object_name = 'item_list'
    paginate_by = 12

    def get_queryset(self):
        # Only active items that are not variants (we'll show variants on the detail page)
        queryset = super().get_queryset().filter(is_active=True, is_variant=False)

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

        # If this is a variant, redirect to the parent item
        if self.object.is_variant and self.object.parent_item:
            # This is handled in get() method
            pass

        # Get color variants if this is a parent item or has variants
        if not self.object.is_variant:
            context['color_variants'] = self.object.get_variants()

        # Get related items (excluding variants of this item)
        context['related_items'] = Item.objects.filter(
            category__in=self.object.category.all(),
            is_active=True,
            is_variant=False  # Only show parent items as related
        ).exclude(id=self.object.id).exclude(
            variants__id=self.object.id  # Exclude items that this item is a variant of
        )[:6]

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

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # If this is a variant, redirect to the parent item
        if self.object.is_variant and self.object.parent_item:
            return redirect('item-detail', pk=self.object.parent_item.id)

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class MerchandiserShopView(LoginRequiredMixin, ListView):
    model = Item
    template_name = 'ufo_shop/merchandiser_shop.html'
    context_object_name = 'items'
    success_url = reverse_lazy('merchandiser_shop')

    def get_queryset(self):
        # Only show items belonging to the logged-in user
        # For merchandiser view, we want to show all items including variants
        return Item.objects.filter(merchandiser=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()

        # Organize items by parent/variant relationship
        items = self.get_queryset()

        # Get parent items (non-variants)
        parent_items = items.filter(is_variant=False)

        # Create a dictionary of parent items with their variants
        organized_items = []
        for parent in parent_items:
            variants = parent.variants.all()
            organized_items.append({
                'parent': parent,
                'variants': variants,
                'has_variants': variants.exists()
            })

        # Add orphaned variants (variants without a parent or with a parent not owned by this user)
        orphaned_variants = items.filter(
            is_variant=True, 
            parent_item__isnull=True
        )
        for variant in orphaned_variants:
            organized_items.append({
                'parent': variant,
                'variants': [],
                'has_variants': False,
                'is_orphaned_variant': True
            })

        context['organized_items'] = organized_items
        return context


# View for creating a new item
class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = forms.ItemForm  # Use the ItemForm
    template_name = 'ufo_shop/item_form.html'
    success_url = reverse_lazy('merchandiser_shop')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Assign the current logged-in user as the merchandiser
        form.instance.merchandiser = self.request.user

        # Handle color variants
        has_color_variants = form.cleaned_data.get('has_color_variants', False)
        is_variant_of = form.cleaned_data.get('is_variant_of')
        color = form.cleaned_data.get('color')

        # If this is a variant of another item
        if is_variant_of:
            form.instance.parent_item = is_variant_of
            form.instance.is_variant = True
            # Inherit some properties from parent
            form.instance.short_description = is_variant_of.short_description
            form.instance.description = is_variant_of.description
            form.instance.category = is_variant_of.category

        # Save the Item instance
        self.object = form.save()

        # Handle multiple image uploads
        images = self.request.FILES.getlist('images') # 'images' is the name of the form field
        for image_file in images:
            Picture.objects.create(item=self.object, picture=image_file)
            # The Picture model's save() method will handle thumbnails/squares

        # If parent item has images and this is a variant with no images, copy parent images
        if is_variant_of and not images:
            parent_pictures = Picture.objects.filter(item=is_variant_of)
            for parent_pic in parent_pictures:
                # Create a copy of the parent picture for this variant
                new_pic = Picture(
                    item=self.object,
                    user=self.request.user,
                    picture=parent_pic.picture,
                    thumbnail=parent_pic.thumbnail,
                    square_image=parent_pic.square_image
                )
                new_pic.save()

        # Use the success_url defined on the class
        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if this is a variant creation
        is_variant_of = self.request.GET.get('is_variant_of')
        if is_variant_of:
            try:
                parent_item = Item.objects.get(id=is_variant_of, merchandiser=self.request.user)
                context['form_title'] = f'Create Color Variant for {parent_item.name}'
                context['parent_item'] = parent_item
            except Item.DoesNotExist:
                context['form_title'] = 'Create New Item'
        else:
            context['form_title'] = 'Create New Item'

        return context

    def get_initial(self):
        initial = super().get_initial()

        # Check if this is a variant creation
        is_variant_of = self.request.GET.get('is_variant_of')
        if is_variant_of:
            try:
                parent_item = Item.objects.get(id=is_variant_of, merchandiser=self.request.user)
                # Pre-fill form with parent item data
                initial['is_variant_of'] = parent_item
                initial['name'] = parent_item.name
                initial['price'] = parent_item.price
                initial['short_description'] = parent_item.short_description
                initial['description'] = parent_item.description
                initial['category'] = parent_item.category.all()
                initial['locations'] = parent_item.locations.all()
            except Item.DoesNotExist:
                pass

        return initial


# View for updating an existing item
class ItemUpdateView(LoginRequiredMixin, UpdateView):
    model = Item
    form_class = forms.ItemForm  # Use the ItemForm instead of fields
    template_name = 'ufo_shop/item_form.html'
    success_url = reverse_lazy('merchandiser_shop')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        # Ensure users can only edit their own items
        queryset = super().get_queryset()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(merchandiser=self.request.user)

    def form_valid(self, form):
        # Handle color variants
        has_color_variants = form.cleaned_data.get('has_color_variants', False)
        is_variant_of = form.cleaned_data.get('is_variant_of')
        color = form.cleaned_data.get('color')

        # If this is a variant of another item
        if is_variant_of and not self.object.is_variant:
            # This is becoming a variant
            form.instance.parent_item = is_variant_of
            form.instance.is_variant = True
            # Inherit some properties from parent
            form.instance.short_description = is_variant_of.short_description
            form.instance.description = is_variant_of.description
            form.instance.category = is_variant_of.category
        elif not is_variant_of and self.object.is_variant:
            # This is no longer a variant
            form.instance.parent_item = None
            form.instance.is_variant = False

        # Save the updated Item instance
        self.object = form.save()

        # Handle *new* multiple image uploads
        images = self.request.FILES.getlist('images') # 'images' is the name of the form field
        for image_file in images:
            Picture.objects.create(item=self.object, picture=image_file)
            # The Picture model's save() method will handle thumbnails/squares

        # If parent item has images and this is a variant with no images, copy parent images
        if is_variant_of and not self.object.pictures.exists():
            parent_pictures = Picture.objects.filter(item=is_variant_of)
            for parent_pic in parent_pictures:
                # Create a copy of the parent picture for this variant
                new_pic = Picture(
                    item=self.object,
                    user=self.request.user,
                    picture=parent_pic.picture,
                    thumbnail=parent_pic.thumbnail,
                    square_image=parent_pic.square_image
                )
                new_pic.save()

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
        cart_items = cart.orderitem_set.all().select_related('item')
        context['cart'] = cart
        context['cart_items'] = cart_items
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        cart = self.get_cart()
        kwargs['cart_items'] = cart.orderitem_set.all().select_related('item')
        return kwargs

    def form_valid(self, form):
        cart = self.get_cart()

        # Update the cart with contact and payment information
        for field in form.cleaned_data:
            if field in ['contact_email', 'contact_phone', 'payment_method', 'needs_receipt']:
                setattr(cart, field, form.cleaned_data[field])

        # Update the status to ORDERED
        cart.status = Order.Status.ORDERED
        cart.calculate_totals()
        cart.save()

        # Update the pickup locations for each order item
        cart_items = cart.orderitem_set.all()
        for item in cart_items:
            pickup_location = form.get_pickup_location(item.id)
            if pickup_location:
                item.pickup_location = pickup_location
                item.save()

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
            'BANK_ACCOUNT': BANK_ACCOUNT,
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
        context['BANK_ACCOUNT'] = BANK_ACCOUNT
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


class MerchandiserStatsView(LoginRequiredMixin, TemplateView):
    """View to display statistics for merchandisers about their sold items"""
    template_name = 'ufo_shop/merchandiser_stats.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if user is a merchandiser
        if not request.user.is_merchandiser:
            messages.error(request, "You need to be a merchandiser to access this page.")
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        merchandiser = self.request.user

        # Get all completed orders containing items from this merchandiser
        # We consider PAID, SHIPPED, and FULFILLED statuses as completed
        completed_statuses = [Order.Status.PAID, Order.Status.SHIPPED, Order.Status.FULFILLED]

        # Get all order items for this merchandiser's items with completed orders
        order_items = OrderItem.objects.filter(
            item__merchandiser=merchandiser,
            order__status__in=completed_statuses
        ).select_related('item', 'order')

        # Total sales
        total_sales = order_items.aggregate(
            total_items=Sum('amount'),
            total_revenue=Sum(F('amount') * F('item__price'))
        )

        # Top selling items
        top_items = order_items.values(
            'item__id', 'item__name'
        ).annotate(
            total_sold=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price'))
        ).order_by('-total_sold')[:10]

        # Sales over time (by month)
        sales_by_month = order_items.annotate(
            month=TruncMonth('order__created_at')
        ).values('month').annotate(
            total_items=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price'))
        ).order_by('month')

        # Recent sales
        recent_sales = order_items.order_by('-order__created_at')[:10]

        context.update({
            'total_sales': total_sales,
            'top_items': top_items,
            'sales_by_month': sales_by_month,
            'recent_sales': recent_sales,
        })

        return context


class AdminStatsView(UserPassesTestMixin, TemplateView):
    """View to display global statistics for admin users"""
    template_name = 'ufo_shop/admin_stats.html'

    def test_func(self):
        # Only allow superusers to access this view
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get sort parameter from request
        sort_by = self.request.GET.get('sort_by', 'revenue')
        sort_order = self.request.GET.get('sort_order', 'desc')

        # Determine sort field and direction
        sort_field = '-revenue' if sort_by == 'revenue' and sort_order == 'desc' else 'revenue'
        if sort_by == 'items':
            sort_field = '-total_items' if sort_order == 'desc' else 'total_items'
        elif sort_by == 'merchandiser':
            sort_field = '-item__merchandiser__email' if sort_order == 'desc' else 'item__merchandiser__email'

        # Get all completed orders
        completed_statuses = [Order.Status.PAID, Order.Status.SHIPPED, Order.Status.FULFILLED]

        # Get all order items with completed orders
        order_items = OrderItem.objects.filter(
            order__status__in=completed_statuses
        ).select_related('item', 'order')

        # Global total sales
        total_sales = order_items.aggregate(
            total_items=Sum('amount'),
            total_revenue=Sum(F('amount') * F('item__price')),
            total_merchandisers=Count('item__merchandiser', distinct=True)
        )

        # Top selling items globally
        top_items = order_items.values(
            'item__id', 'item__name', 'item__merchandiser__email'
        ).annotate(
            total_sold=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price'))
        ).order_by('-total_sold')[:10]

        # Top merchandisers
        top_merchandisers = order_items.values(
            'item__merchandiser__id', 'item__merchandiser__email', 'item__merchandiser__first_name', 
            'item__merchandiser__last_name'
        ).annotate(
            total_items=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price')),
            unique_items=Count('item', distinct=True)
        ).order_by(sort_field)[:10]

        # Sales over time (by month)
        sales_by_month = order_items.annotate(
            month=TruncMonth('order__created_at')
        ).values('month').annotate(
            total_items=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price')),
            merchandiser_count=Count('item__merchandiser', distinct=True)
        ).order_by('month')

        # Sales by category
        sales_by_category = order_items.values(
            'item__category__name'
        ).annotate(
            total_items=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price'))
        ).order_by('-revenue')

        # Sales by merchandiser by month
        sales_by_merchandiser_by_month = order_items.annotate(
            month=TruncMonth('order__created_at')
        ).values(
            'month', 'item__merchandiser__email'
        ).annotate(
            total_items=Sum('amount'),
            revenue=Sum(F('amount') * F('item__price'))
        ).order_by('month', '-revenue')

        context.update({
            'total_sales': total_sales,
            'top_items': top_items,
            'top_merchandisers': top_merchandisers,
            'sales_by_month': sales_by_month,
            'sales_by_category': sales_by_category,
            'sales_by_merchandiser_by_month': sales_by_merchandiser_by_month,
            'sort_by': sort_by,
            'sort_order': sort_order,
        })

        return context
