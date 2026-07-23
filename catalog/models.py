from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Brand(models.Model):
    """A distributed brand shown on the homepage and catalog."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    logo = models.CharField(
        max_length=255,
        blank=True,
        help_text="Path under static/, e.g. assets/images/brands/oishi.png",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    # Match keywords used when importing Excel rows
    match_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated name prefixes for Excel matching",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.replace("'", "").replace("!", ""))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:brand_detail", kwargs={"slug": self.slug})

    @property
    def product_count(self) -> int:
        return self.products.filter(is_active=True).count()

    def keyword_list(self) -> list[str]:
        if not self.match_keywords:
            return [self.name.lower()]
        return [k.strip().lower() for k in self.match_keywords.split(",") if k.strip()]


class Category(models.Model):
    """Optional product group within a brand (left sidebar filters)."""

    brand = models.ForeignKey(
        Brand, related_name="categories", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"
        unique_together = [("brand", "slug")]

    def __str__(self) -> str:
        return f"{self.brand.name} / {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Showcase item — gram/size variants are collapsed on import."""

    brand = models.ForeignKey(Brand, related_name="products", on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255, help_text="Display name without weight/size")
    full_name = models.CharField(max_length=255, blank=True, help_text="Original Excel name")
    sku = models.CharField(max_length=64, blank=True, db_index=True)
    unit = models.CharField(max_length=32, default="PCS")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    dedupe_key = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Normalized key used to collapse size variants",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        unique_together = [("brand", "dedupe_key")]

    def __str__(self) -> str:
        return f"{self.brand.name} — {self.name}"
