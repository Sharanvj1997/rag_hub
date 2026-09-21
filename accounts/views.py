from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer

User = get_user_model()


# ---------- API views ----------

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    print('calling register',request.data)
    serializer = RegisterSerializer(data=request.data)
    

    if serializer.is_valid():
        print('yes validated')
        user = serializer.save()
        return Response(
            {
                "success": True,
                "message": "User registered successfully.",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        {"success": False, "errors": serializer.errors},
        status=status.HTTP_400_BAD_REQUEST,
    )


class LoginView(TokenObtainPairView):
    """
    POST { "email": ..., "password": ... }
    Returns { "access": ..., "refresh": ..., "user": {...} }
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    POST { "refresh": "<refresh_token>" }
    Blacklists the refresh token so it can no longer be used.
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {"success": True, "message": "Logged out successfully."},
            status=status.HTTP_205_RESET_CONTENT,
        )
    except Exception:
        return Response(
            {"success": False, "message": "Invalid or missing refresh token."},
            status=status.HTTP_400_BAD_REQUEST,
        )



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    return Response({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "profile_picture": user.profile_picture.url if user.profile_picture else None,
    })

# ---------- Page views (render templates that call the API via JS) ----------

def register_page(request):
    return render(request, "accounts/register.html")


def login_page(request):
    return render(request, "accounts/login.html")