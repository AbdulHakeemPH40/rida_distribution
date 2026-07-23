from django.conf import settings


def site_globals(request):
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "R i D A"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", ""),
        "SITE_PHONE": getattr(settings, "SITE_PHONE", ""),
        "SITE_PHONE_DISPLAY": getattr(settings, "SITE_PHONE_DISPLAY", ""),
        "SITE_EMAIL": getattr(settings, "SITE_EMAIL", ""),
        "SITE_WHATSAPP": getattr(settings, "SITE_WHATSAPP", ""),
        "SITE_ADDRESS": getattr(settings, "SITE_ADDRESS", ""),
        "SITE_DOMAIN": getattr(settings, "SITE_DOMAIN", ""),
    }
