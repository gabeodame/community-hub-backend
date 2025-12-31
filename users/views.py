from rest_framework import generics, permissions, response, status
from rest_framework_simplejwt.views import TokenObtainPairView

from users.serializers import RegisterSerializer, UserMeSerializer
from users.throttles import LoginThrottle, RegisterThrottle, UserWriteThrottle


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            if "username" in serializer.errors or "email" in serializer.errors:
                return response.Response(
                    {"detail": "Unable to register with provided credentials."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            error_key = None
            if "detail" in serializer.errors:
                error_key = "detail"
            elif "non_field_errors" in serializer.errors:
                error_key = "non_field_errors"

            if error_key:
                detail = serializer.errors[error_key]
                if isinstance(detail, list) and detail:
                    detail = detail[0]
                return response.Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserWriteThrottle]

    def get_object(self):
        return self.request.user
