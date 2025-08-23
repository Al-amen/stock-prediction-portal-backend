from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # This will authenticate using email & password
        data = super().validate(attrs)

        if not self.user.is_active:
            raise serializers.ValidationError({"detail": "Please verify your email before logging in."})

        return data

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    password1 = serializers.CharField(write_only=True,style={'input_type': 'password'})
    class Meta:
        model = User
        fields = ['username','email','password','password1']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password1']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password1")  # Remove confirmation field
        user = User.objects.create_user(
            **validated_data,
            password=password  # passes to your manager
        )
        return user



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Optional: check if user exists
        if not User.objects.filter(email=value).exists():
            # Don't reveal user existence
            pass
        return value
        


class PasswordResetConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True,style={'input_type': 'password'})

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs['uidb64']))
            self.user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "Invalid UID"})

        if not PasswordResetTokenGenerator().check_token(self.user, attrs['token']):
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match"})

        return attrs

    def save(self):
        password = self.validated_data['new_password']
        self.user.set_password(password)
        self.user.save()
        return self.user



class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True,style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True,style={'input_type': 'password'})

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is incorrect"})

        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New passwords do not match"})

        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as old password"})

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user