from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from authemail import views


urlpatterns = [
    url(r'^signup/$', views.Signup.as_view(), name='authemail-signup'),
    url(r'^signup/verify/$', views.SignupVerify.as_view(),
        name='authemail-signup-verify'),

    url(r'^login/$', views.Login.as_view(), name='authemail-login'),
    url(r'^logout/$', views.Logout.as_view(), name='authemail-logout'),

    url(r'^password/reset/$', views.PasswordReset.as_view(), 
        name='authemail-password-reset'),
    url(r'^password/reset/verify/$', views.PasswordResetVerify.as_view(), 
        name='authemail-password-reset-verify'),
    url(r'^password/reset/verified/$', views.PasswordResetVerified.as_view(), 
        name='authemail-password-reset-verified'),
    url(r'^password/change/$', views.PasswordChange.as_view(), 
        name='authemail-password-change'),

    url(r'^users/me/$', views.UserMe.as_view(), name='authemail-me'),
]


urlpatterns = format_suffix_patterns(urlpatterns)
