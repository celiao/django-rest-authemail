from django.contrib import admin
from django.urls import include, path
from . import views

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/accounts/', include('accounts.urls')),
    path('api/accounts/', include('authemail.urls')),

    path('landing/', views.LandingFrontEnd.as_view(), name='landing_page'),

    path('signup/', views.SignupFrontEnd.as_view(), name='signup_page'),
    path('signup/email_sent/', views.SignupEmailSentFrontEnd.as_view(),
         name='signup_email_sent_page'),
    path('signup/verify/', views.SignupVerifyFrontEnd.as_view()),
    path('signup/verified/', views.SignupVerifiedFrontEnd.as_view(),
         name='signup_verified_page'),
    path('signup/not_verified/', views.SignupNotVerifiedFrontEnd.as_view(),
         name='signup_not_verified_page'),

    path('login/', views.LoginFrontEnd.as_view(), name='login_page'),
    path('home/', views.HomeFrontEnd.as_view(), name='home_page'),
    path('logout/', views.LogoutFrontEnd.as_view(), name='logout_page'),

    path('password/reset/', views.PasswordResetFrontEnd.as_view(),
         name='password_reset_page'),
    path('password/reset/email_sent/',
         views.PasswordResetEmailSentFrontEnd.as_view(),
         name='password_reset_email_sent_page'),
    path('password/reset/verify/', views.PasswordResetVerifyFrontEnd.as_view()),
    path('password/reset/verified/',
         views.PasswordResetVerifiedFrontEnd.as_view(),
         name='password_reset_verified_page'),
    path('password/reset/not_verified/',
         views.PasswordResetNotVerifiedFrontEnd.as_view(),
         name='password_reset_not_verified_page'),
    path('password/reset/success/', views.PasswordResetSuccessFrontEnd.as_view(),
         name='password_reset_success_page'),

    path('email/change/', views.EmailChangeFrontEnd.as_view(),
         name='email_change_page'),
    path('email/change/emails_sent/',
         views.EmailChangeEmailsSentFrontEnd.as_view(),
         name='email_change_emails_sent_page'),
    path('email/change/verify/', views.EmailChangeVerifyFrontEnd.as_view()),
    path('email/change/verified/',
         views.EmailChangeVerifiedFrontEnd.as_view(),
         name='email_change_verified_page'),
    path('email/change/not_verified/',
         views.EmailChangeNotVerifiedFrontEnd.as_view(),
         name='email_change_not_verified_page'),

    path('password/change/', views.PasswordChangeFrontEnd.as_view(),
         name='password_change_page'),
    path('password/change/success/', views.PasswordChangeSuccessFrontEnd.as_view(),
         name='password_change_success_page'),

    path('users/me/change/', views.UsersMeChangeFrontEnd.as_view(),
         name='users_me_change_page'),
    path('users/me/change/success/', views.UsersMeChangeSuccessFrontEnd.as_view(),
         name='users_me_change_success_page'),
]
