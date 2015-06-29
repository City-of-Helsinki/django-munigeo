from django.conf import settings


def get_default_srid():
    if hasattr(settings, 'DEFAULT_SRID'):
        srid = settings.DEFAULT_SRID
    elif hasattr(settings, 'PROJECTION_SRID'):
        srid = settings.PROJECTION_SRID
    else:
        # If SRID not configured in settings, use WGS-84.
        srid = 4326

    return srid
