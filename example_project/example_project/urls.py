from django.contrib import admin
from django.urls import include, path
from . import views

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/accounts/', include('accounts.urls')),
    path('api/accounts/', include('authemail.urls')),

    path('landing/', views.LandingView.as_view(), name='landing_page'),

    path('signup/', views.SignupView.as_view(), name='signup_page'),
    path('signup/email_sent/', views.SignupEmailSentView.as_view(),
        name='signup_email_sent_page'),
    path('signup/verify/', views.SignupVerifyView.as_view()),
    path('signup/verified/', views.SignupVerifiedView.as_view(),
        name='signup_verified_page'),
    path('signup/not_verified/', views.SignupNotVerifiedView.as_view(),
        name='signup_not_verified_page'),

    path('login/', views.LoginView.as_view(), name='login_page'),
    path('home/', views.HomeView.as_view(), name='home_page'),
    path('logout/', views.LogoutView.as_view(), name='logout_page'),

    path('password/reset/', views.PasswordResetView.as_view(),
        name='password_reset_page'),
    path('password/reset/email_sent/',
        views.PasswordResetEmailSentView.as_view(),
        name='password_reset_email_sent_page'),
    path('password/reset/verify/', views.PasswordResetVerifyView.as_view()),
    path('password/reset/verified/',
        views.PasswordResetVerifiedView.as_view(),
        name='password_reset_verified_page'),
    path('password/reset/not_verified/',
        views.PasswordResetNotVerifiedView.as_view(),
        name='password_reset_not_verified_page'),
    path('password/reset/success/', views.PasswordResetSuccessView.as_view(),
        name='password_reset_success'),

    path('password/change/', views.PasswordChangeView.as_view(),
        name='password_change_page'),

    path('users/me/change/', views.UsersMeChangeView.as_view(),
        name='users_me_change_page'),
    path('users/me/change/success/', views.UsersMeChangeSuccessView.as_view(),
        name='users_me_change_success'),
]
