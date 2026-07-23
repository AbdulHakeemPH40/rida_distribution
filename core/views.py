from django.shortcuts import render
from django.views.generic import TemplateView

from catalog.models import Brand


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands"] = Brand.objects.filter(is_active=True).order_by(
            "sort_order", "name"
        )
        return ctx


class AboutView(TemplateView):
    template_name = "core/about.html"


class WhyRidaView(TemplateView):
    template_name = "core/why_rida.html"
