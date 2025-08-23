from django.shortcuts import render
from rest_framework.views import APIView
from django.shortcuts import redirect
from rest_framework import generics,status,permissions
from .utils import generate_email_verification_token
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken,TokenError
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from accounts import serializers as accounts_serializers

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    serializer_class = accounts_serializers.RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if an active user with the same email already exists
        if User.objects.filter(email=serializer.validated_data['email'], is_active=True).exists():
            return Response({"message": "User already exists with this email", "icon": "warning"},
                            status=status.HTTP_409_CONFLICT)

        user = serializer.save()  # Save inactive user

        # Generate verification token
        token = generate_email_verification_token(user)

        # Create frontend verification link
        verify_link = f"http://localhost:5173/verify-email/?token={token}"

        # Send verification email
        send_mail(
            subject="Verify your email",
            message=f"Hi {user.username or ''}, click to verify your account: {verify_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response(
            {"message": "Registration successful. Check your email to verify your account.", "icon": "success"},
            status=status.HTTP_201_CREATED
        )


class VerifyEmailAPIView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
     #   print("token", token)
        if not token:
            #print("token not found")
            return Response({"message": "Token missing", "icon": "error"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = AccessToken(token)  # <-- MUST use AccessToken

            if not payload.get('email_verification'):
                return Response({"message": "Invalid verification token", "icon": "warning"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=payload['user_id'])

            if user.is_active:
                return Response({"message": "Account already verified", "icon": "info"}, status=status.HTTP_200_OK)

            user.is_active = True
            user.save()

            return Response({"message": "Email verified successfully", "icon": "success"}, status=status.HTTP_200_OK)

        except TokenError as e:
            return Response({"message": "Token is invalid or expired", "icon": "error"}, status=status.HTTP_400_BAD_REQUEST)
            
    
        
class ResendVerificationAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email, is_active=False)
            token = generate_email_verification_token(user)
            verify_link = f"http://localhost:5173/resend-verify-email/?token={token}"
            send_mail(
                "Verify your email",
                f"Click to verify: {verify_link}",
                settings.EMAIL_HOST_USER,
                [user.email]
            )
            return Response({"message": "Verification email resent.","icon":"info"}, status=200)
        except User.DoesNotExist:
            return Response({"message": "No inactive account found with that email.","icon":"warning"}, status=404)

        

class LoginAPIView(TokenObtainPairView):
    serializer_class = accounts_serializers.CustomTokenObtainPairSerializer
    


class PasswordResetRequestAPIView(APIView):
    serializer_class = accounts_serializers.PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"http://localhost:5173/reset-password/{uidb64}/{token}/"

            send_mail(
                subject="Password Reset",
                message=f"Click the link to reset your password: {reset_link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
        except User.DoesNotExist:
            pass  # don't reveal that the user doesn't exist

        return Response({"message": "If the email exists, a reset link will be sent.","icon":"info"}, status=status.HTTP_200_OK)
    



class PasswordResetConfirmAPIView(APIView):
    def post(self, request,uidb64, token):
        serializer = accounts_serializers.PasswordResetConfirmSerializer(data={
            "uidb64": uidb64,
            "token": token,
            "new_password": request.data.get("new_password"),
            "confirm_password": request.data.get("confirm_password"),
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password has been reset successfully.","icon":"success"}, status=status.HTTP_200_OK)



class ChangePasswordAPIView(generics.UpdateAPIView):
    serializer_class = accounts_serializers.ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Password updated successfully","icon":"info"}, status=status.HTTP_200_OK)