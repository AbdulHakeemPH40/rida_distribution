from django.contrib import admin
from .models import Brand, Category, Product


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ("name", "sku", "unit", "price", "stock", "is_active")
    show_change_link = True


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CategoryInline, ProductInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "sort_order")
    list_filter = ("brand",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "sku", "unit", "price", "stock", "is_active")
    list_filter = ("brand", "is_active", "unit")
    search_fields = ("name", "full_name", "sku")
    list_select_related = ("brand", "category")
