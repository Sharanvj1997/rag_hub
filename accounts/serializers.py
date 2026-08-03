from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data