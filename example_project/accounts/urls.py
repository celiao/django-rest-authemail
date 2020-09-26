from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from accounts import views


urlpatterns = [
    path('users/me/', views.MyUserMe.as_view()),
]


urlpatterns = format_suffix_patterns(urlpatterns)
