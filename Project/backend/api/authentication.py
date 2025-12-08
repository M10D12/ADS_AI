from rest_framework_simplejwt.authentication import JWTAuthentication
from api.models import Usuario
from rest_framework import exceptions

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token["user_id"]
        except KeyError:
            raise exceptions.AuthenticationFailed("Token inválido")
        try:
            user = Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            raise exceptions.AuthenticationFailed("Usuário não registado")

        return user
