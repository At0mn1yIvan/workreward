from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import ManagerCode
from rest_framework_simplejwt.tokens import RefreshToken
from .renderers import UserJSONRenderer
from .serializers import (
    LoginUserSerializer,
    ManagerCodeSerializer,
    RegisterUserSerializer,
)


class GetUsersAPIView(viewsets.ModelViewSet):
    queryset = ManagerCode.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ManagerCodeSerializer


class RegisterAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = RegisterUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }, status=status.HTTP_200_OK)
