import string

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView, TemplateView

from .models import Brand, Category, Product


class BrandListView(ListView):
    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"

    def get_queryset(self):
        qs = (
            Brand.objects.filter(is_active=True)
            .annotate(
                n_products=Count("products", filter=Q(products__is_active=True)),
            )
        )

        # Search
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(slug__icontains=q)
                | Q(description__icontains=q)
            )

        # Alphabet filter
        letter = self.request.GET.get("letter", "").strip().upper()
        if letter and len(letter) == 1 and letter in string.ascii_uppercase:
            qs = qs.filter(name__istartswith=letter)

        # Sort
        sort = self.request.GET.get("sort", "name").strip()
        valid_sorts = {"name", "-name", "-n_products", "n_products"}
        if sort not in valid_sorts:
            sort = "name"
        if sort == "name":
            qs = qs.order_by("sort_order", "name")
        elif sort == "-name":
            qs = qs.order_by("-name")
        elif sort == "-n_products":
            qs = qs.order_by("-n_products", "name")
        elif sort == "n_products":
            qs = qs.order_by("n_products", "name")
        else:
            qs = qs.order_by("sort_order", "name")

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Available alphabet letters (prefetch counts)
        all_brands = Brand.objects.filter(is_active=True)
        letter_counts = (
            all_brands.values_list("name", flat=True)
            .annotate()  # no-op to reset grouping
        )
        available = set()
        for name in all_brands.values_list("name", flat=True):
            first = name[0].upper() if name else ""
            if first in string.ascii_uppercase:
                available.add(first)

        ctx["alphabet"] = list(string.ascii_uppercase)
        ctx["available_letters"] = available
        ctx["active_letter"] = self.request.GET.get("letter", "").strip().upper() or None
        ctx["search_q"] = self.request.GET.get("q", "").strip()
        ctx["sort"] = self.request.GET.get("sort", "").strip() or "name"
        ctx["total_products"] = Product.objects.filter(
            brand__is_active=True, is_active=True
        ).count()

        return ctx


class BrandDetailView(DetailView):
    """Product showcase page: simple search + sort, flat product grid."""

    model = Brand
    template_name = "catalog/brand_detail.html"
    context_object_name = "brand"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Brand.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        brand = self.object
        q = self.request.GET.get("q", "").strip()
        sort = self.request.GET.get("sort", "name").strip()

        products = Product.objects.filter(brand=brand, is_active=True)

        if q:
            products = products.filter(
                Q(name__icontains=q) | Q(full_name__icontains=q) | Q(sku__icontains=q)
            )

        # Sort
        if sort == "-name":
            products = products.order_by("-name")
        else:
            products = products.order_by("sort_order", "name")

        ctx.update(
            {
                "products": products,
                "search_q": q,
                "sort": sort,
                "product_count": products.count(),
                "total_count": Product.objects.filter(
                    brand=brand, is_active=True
                ).count(),
            }
        )
        return ctx


class HomeBrandsPartial:
    """Helper used by home view — not a URL view."""

    @staticmethod
    def brands_queryset():
        return Brand.objects.filter(is_active=True).order_by("sort_order", "name")
