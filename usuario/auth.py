from ninja.security import HttpBearer
from usuario.models import Usuario


class AuthBearer(HttpBearer):
    """Autenticación Bearer para Ninja.

    Devuelve la instancia `Usuario` si el token es válido, o `None`.
    """

    def authenticate(self, request, token):
        if not token:
            return None
        # token recibido ya es la parte después de 'Bearer '
        user = Usuario.objects.filter(token=token).first()
        if not user:
            return None
        return user