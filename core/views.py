from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import DatabaseError, OperationalError
import json
import logging

logger = logging.getLogger(__name__)

from .models import (
    Product, MacroCategory, Category, SubCategory,
    Brand, Quote, QuoteItem, ContactMessage
)
from .forms import QuoteForm, ContactForm
from .utils import Cart


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Handle database errors gracefully
        try:
            context['featured_products'] = list(Product.objects.filter(
                featured=True, is_active=True
            )[:8])
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch featured products: {e}")
            context['featured_products'] = []

        try:
            context['macro_categories'] = list(MacroCategory.objects.annotate(
                product_count=Count('products')
            ))
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch macro categories: {e}")
            context['macro_categories'] = []

        try:
            context['brands'] = list(Brand.objects.all()[:6])
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch brands: {e}")
            context['brands'] = []

        return context


class ProductListView(ListView):
    model = Product
    template_name = 'core/product_list.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search) |
                Q(brand__name__icontains=search)
            )

        # Filters
        macro = self.request.GET.get('macro')
        if macro:
            queryset = queryset.filter(macro_category__slug=macro)

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        subcategory = self.request.GET.get('subcategory')
        if subcategory:
            queryset = queryset.filter(subcategory__slug=subcategory)

        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand__slug=brand)

        # Sorting
        sort = self.request.GET.get('sort', 'name')
        if sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == '-name':
            queryset = queryset.order_by('-name')
        elif sort == 'price':
            queryset = queryset.order_by('price')
        elif sort == '-price':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['macro_categories'] = MacroCategory.objects.annotate(
                product_count=Count('products')
            )
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch macro categories: {e}")
            context['macro_categories'] = []

        try:
            context['categories'] = Category.objects.annotate(
                product_count=Count('products')
            )
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch categories: {e}")
            context['categories'] = []

        try:
            context['brands'] = Brand.objects.annotate(
                product_count=Count('products')
            )
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch brands: {e}")
            context['brands'] = []

        context['current_filters'] = self.request.GET
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'core/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Related products from same category
        try:
            context['related_products'] = Product.objects.filter(
                category=self.object.category,
                is_active=True
            ).exclude(id=self.object.id)[:4]
        except (DatabaseError, OperationalError, Exception) as e:
            logger.warning(f"Could not fetch related products: {e}")
            context['related_products'] = []
        return context


def category_view(request, macro_slug, category_slug=None):
    macro = get_object_or_404(MacroCategory, slug=macro_slug)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, macro_category=macro)
        products = Product.objects.filter(category=category, is_active=True)
        title = category.name
    else:
        category = None
        products = Product.objects.filter(macro_category=macro, is_active=True)
        title = macro.name

    # Pagination
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        'macro_category': macro,
        'category': category,
        'products': products,
        'title': title,
        'subcategories': SubCategory.objects.filter(category=category) if category else None,
    }
    return render(request, 'core/category.html', context)


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)

    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/cart_button.html', {
            'product': product,
            'in_cart': True
        })

    messages.success(request, _('Product added to cart'))
    return redirect('product_detail', slug=product.slug)


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)

    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/cart_items.html', {
            'cart': cart
        })

    messages.success(request, _('Product removed from cart'))
    return redirect('cart_detail')


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'core/cart_detail.html', {'cart': cart})


def quote_request(request):
    cart = Cart(request)

    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            quote = form.save()

            # Add cart items to quote
            for item in cart:
                QuoteItem.objects.create(
                    quote=quote,
                    product=item['product'],
                    quantity=item['quantity']
                )

            # Clear cart
            cart.clear()

            # Send confirmation email (placeholder)
            messages.success(request, _(
                'Your quote request has been submitted. '
                'We will contact you shortly with a quotation.'
            ))
            return redirect('quote_success', quote_id=quote.id)
    else:
        form = QuoteForm()

    return render(request, 'core/quote_request.html', {
        'form': form,
        'cart': cart
    })


def quote_success(request, quote_id):
    quote = get_object_or_404(Quote, id=quote_id)
    return render(request, 'core/quote_success.html', {'quote': quote})


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your message has been sent successfully.'))
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


def search(request):
    query = request.GET.get('q', '')
    products = Product.objects.none()

    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(ai_description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(is_active=True).distinct()

    # Pagination
    paginator = Paginator(products, 24)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    return render(request, 'core/search.html', {
        'products': products,
        'query': query,
        'result_count': paginator.count
    })


@require_POST
def update_cart_quantity(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=quantity, update_quantity=True)

    return JsonResponse({
        'success': True,
        'cart_total': len(cart),
        'item_total': quantity * float(product.price) if product.price else 0
    })