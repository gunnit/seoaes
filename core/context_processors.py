from django.conf import settings
from .utils import Cart
from .models import MacroCategory, Brand


def cart_context(request):
    """Add cart to context"""
    return {
        'cart': Cart(request)
    }


def brand_context(request):
    """Add brand information and navigation data to context"""
    try:
        nav_macro_categories = MacroCategory.objects.all()
    except:
        nav_macro_categories = []

    try:
        nav_brands = Brand.objects.all()[:10]
    except:
        nav_brands = []

    return {
        'site_name': 'Maxlube',
        'company_name': 'Maxlube S.r.l.',
        'company_phone': '+39 02 1234567',
        'company_email': 'info@maxlube.it',
        'company_address': 'Via Industriale 123, 20100 Milano, Italia',
        'nav_macro_categories': nav_macro_categories,
        'nav_brands': nav_brands,
        'current_language': 'it',
    }