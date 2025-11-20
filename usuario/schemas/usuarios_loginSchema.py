from ninja import Schema,ModelSchema
from usuario.models import Usuario, PermisosUsuarioTienda
from typing import Optional
from .permisosSchema import PermisosUsuarioTiendaSchema


class UserCreateSchema(Schema):
	username: str
	password: str
	

class ChangePasswordSchema(Schema):
    old_password: str
    new_password: str

class SuperUserResetPasswordSchema(Schema):
    new_password: str


class LoginSchema(Schema):
	username: str
	password: str


class TokenSchema(ModelSchema):
    permisos: Optional[list[PermisosUsuarioTiendaSchema]] = None
    class Meta:
        model = Usuario
        exclude = ['password']
	
class UserOutSchema(ModelSchema):
    permisos: Optional[list[PermisosUsuarioTiendaSchema]] = None
    class Meta:
        model = Usuario
        exclude = ['password', 'token']