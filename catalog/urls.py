from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("brands/", views.BrandListView.as_view(), name="brand_list"),
    path("brands/<slug:slug>/", views.BrandDetailView.as_view(), name="brand_detail"),
]
