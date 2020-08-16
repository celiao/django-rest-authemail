from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from accounts import views


urlpatterns = [
    url(r'^users/me/$', views.MyUserMe.as_view()),
]


urlpatterns = format_suffix_patterns(urlpatterns)
