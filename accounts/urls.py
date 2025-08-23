
from rest_framework_simplejwt.views import  TokenRefreshView
from django.urls import path
from .import views

urlpatterns = [
   #Authentication Endpoint
   path("user/login/", views.LoginAPIView.as_view(), name="login"),
   path("user/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
   path('user/register/',views.RegisterAPIView.as_view()),
   path('user/verify-email/', views.VerifyEmailAPIView.as_view(), name='verify-email'),
   path('user/resend-verify-email/',views.ResendVerificationAPIView.as_view(),name='resend-verify-email'),
   path("user/password-reset/", views.PasswordResetRequestAPIView.as_view(), name="password_reset"),
   path("user/reset-password-confirm/<uidb64>/<token>/", views.PasswordResetConfirmAPIView.as_view(), name="reset-password-confirm"),
   path('user/password-change/',views.ChangePasswordAPIView.as_view(),name='password-change')
   
  
]
