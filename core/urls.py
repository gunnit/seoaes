from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path('', views.HomeView.as_view(), name='home'),

    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    # Categories
    path('category/<slug:macro_slug>/', views.category_view, name='macro_category'),
    path('category/<slug:macro_slug>/<slug:category_slug>/', views.category_view, name='category'),

    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/', views.update_cart_quantity, name='update_cart_quantity'),

    # Quote
    path('quote/', views.quote_request, name='quote_request'),
    path('quote/success/<int:quote_id>/', views.quote_success, name='quote_success'),

    # Contact
    path('contact/', views.contact, name='contact'),

    # Search
    path('search/', views.search, name='search'),
]