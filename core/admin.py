from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    Brand, MacroCategory, Category, SubCategory,
    Product, Quote, QuoteItem, ContactMessage
)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')


@admin.register(MacroCategory)
class MacroCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'slug', 'category_count', 'product_count']
    search_fields = ['name', 'name_en']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'name_en', 'slug', 'image')
        }),
        (_('Descriptions'), {
            'fields': ('description', 'description_en')
        }),
    )

    def category_count(self, obj):
        return obj.categories.count()
    category_count.short_description = _('Categories')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'macro_category', 'subcategory_count', 'product_count']
    list_filter = ['macro_category']
    search_fields = ['name', 'name_en', 'macro_category__name']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['macro_category']
    fieldsets = (
        (None, {
            'fields': ('macro_category', 'name', 'name_en', 'slug', 'image')
        }),
        (_('Descriptions'), {
            'fields': ('description', 'description_en')
        }),
    )

    def subcategory_count(self, obj):
        return obj.subcategories.count()
    subcategory_count.short_description = _('Subcategories')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'category', 'product_count']
    list_filter = ['category__macro_category', 'category']
    search_fields = ['name', 'name_en', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['category']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'name_en', 'slug')
        }),
        (_('Descriptions'), {
            'fields': ('description', 'description_en')
        }),
    )

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = _('Products')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'category', 'price',
        'in_stock', 'featured', 'is_active', 'image_preview'
    ]
    list_filter = [
        'is_active', 'featured', 'in_stock',
        'brand', 'macro_category', 'category', 'subcategory'
    ]
    search_fields = ['name', 'sku', 'description', 'ai_description']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['brand', 'macro_category', 'category', 'subcategory']
    list_editable = ['featured', 'is_active', 'in_stock', 'price']
    readonly_fields = ['created_at', 'updated_at', 'image_preview_large']

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'sku', 'brand')
        }),
        (_('Categories'), {
            'fields': ('macro_category', 'category', 'subcategory')
        }),
        (_('Descriptions'), {
            'fields': ('description', 'description_en', 'ai_description', 'ai_description_en')
        }),
        (_('Additional Info'), {
            'fields': ('application', 'application_en', 'observation', 'notes')
        }),
        (_('Pricing & Stock'), {
            'fields': ('price', 'in_stock', 'stock_quantity')
        }),
        (_('Images'), {
            'fields': ('image', 'image_2', 'image_3', 'image_4', 'image_preview_large')
        }),
        (_('Documents'), {
            'fields': ('datasheet', 'safety_sheet')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Settings'), {
            'fields': ('featured', 'is_active', 'created_at', 'updated_at')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 50px; width: auto;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = _('Preview')

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height: 200px; width: auto;"/>',
                obj.image.url
            )
        return '-'
    image_preview_large.short_description = _('Image Preview')

    actions = ['make_featured', 'remove_featured', 'activate', 'deactivate']

    def make_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured.")
    make_featured.short_description = _("Mark as featured")

    def remove_featured(self, request, queryset):
        queryset.update(featured=False)
        self.message_user(request, f"{queryset.count()} products removed from featured.")
    remove_featured.short_description = _("Remove from featured")

    def activate(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} products activated.")
    activate.short_description = _("Activate products")

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} products deactivated.")
    deactivate.short_description = _("Deactivate products")


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0
    autocomplete_fields = ['product']
    fields = ['product', 'quantity', 'notes']


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'company_name', 'contact_name', 'email',
        'status', 'created_at', 'quoted_amount'
    ]
    list_filter = ['status', 'created_at', 'country']
    search_fields = ['company_name', 'contact_name', 'email', 'vat_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [QuoteItemInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Customer Information'), {
            'fields': (
                'company_name', 'contact_name', 'email',
                'phone', 'vat_number'
            )
        }),
        (_('Address'), {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        (_('Quote Details'), {
            'fields': ('message', 'status', 'quoted_amount', 'admin_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_processing', 'mark_as_quoted']

    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, f"{queryset.count()} quotes marked as processing.")
    mark_as_processing.short_description = _("Mark as processing")

    def mark_as_quoted(self, request, queryset):
        queryset.update(status='quoted')
        self.message_user(request, f"{queryset.count()} quotes marked as quoted.")
    mark_as_quoted.short_description = _("Mark as quoted")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'subject')
        }),
        (_('Message'), {
            'fields': ('message', 'is_read')
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = _("Mark as read")

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} messages marked as unread.")
    mark_as_unread.short_description = _("Mark as unread")


# Customize admin site
admin.site.site_header = "Maxlube Administration"
admin.site.site_title = "Maxlube Admin"
admin.site.index_title = "Welcome to Maxlube Administration"