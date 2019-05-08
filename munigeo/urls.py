from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from munigeo.api import all_views


router = DefaultRouter()
for view in all_views:
    router.register(view['name'], view['class'])

urlpatterns = [
    url(r'^', include(router.urls)),
]
