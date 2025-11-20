from ninja import Router, Header
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpRequest
import uuid

from usuario.models import Usuario
from usuario.schemas.usuarios_loginSchema import (
	LoginSchema,
	TokenSchema,
	UserCreateSchema,
	UserOutSchema,
	ChangePasswordSchema,
	SuperUserResetPasswordSchema,
)
from core.schemas import ErrorSchema

usuario_router = Router()


def _get_superadmin_by_token(raw_auth: str | None):
	if not raw_auth:
		return None
	token = raw_auth.strip()
	if token.lower().startswith("token "):
		token = token.split(" ", 1)[1].strip()
	return Usuario.objects.filter(token=token, es_superusuario=True).first()


def _get_user_by_token(raw_auth: str | None):
	if not raw_auth:
		return None
	token = raw_auth.strip()
	if token.lower().startswith("token "):
		token = token.split(" ", 1)[1].strip()
	return Usuario.objects.filter(token=token).first()


@usuario_router.post("/login/", response={200: TokenSchema, 400: ErrorSchema},auth=None)
def login(request: HttpRequest, payload: LoginSchema):
	user = Usuario.objects.filter(username=payload.username).first()
	if not user or not check_password(payload.password, user.password):
		return 400, {"message": "Credenciales inválidas"}
	token = uuid.uuid4().hex
	user.token = token
	user.save(update_fields=["token"])
	return {"token": token}


@usuario_router.post("/crear/", response={200: UserOutSchema, 401: ErrorSchema, 400: ErrorSchema})
def crear_usuario(request: HttpRequest, payload: UserCreateSchema, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	if Usuario.objects.filter(username=payload.username).exists():
		return 400, {"message": "El nombre de usuario ya existe"}

	usuario = Usuario(
		username=payload.username,
		password=make_password(payload.password),
		es_superusuario=payload.es_superusuario,
	)
	usuario.save()

	# opcional: incluir permisos relacionados si el ModelSchema los resuelve
	return usuario



@usuario_router.put("/password/change/", response={200: dict, 401: ErrorSchema, 400: ErrorSchema})
def change_password(request: HttpRequest, payload: ChangePasswordSchema, authorization: str | None = Header(None)):
	user = _get_user_by_token(authorization)
	if not user:
		return 401, {"message": "Token inválido o no proporcionado"}

	if not check_password(payload.old_password, user.password):
		return 400, {"message": "Contraseña antigua incorrecta"}

	user.password = make_password(payload.new_password)
	user.save(update_fields=["password"])
	return {"message": "Contraseña actualizada"}


@usuario_router.post("/password/reset/{usuario_id}/", response={200: dict, 401: ErrorSchema, 404: ErrorSchema})
def super_reset_password(request: HttpRequest, usuario_id: int, payload: SuperUserResetPasswordSchema, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	usuario = Usuario.objects.filter(id=usuario_id).first()
	if not usuario:
		return 404, {"message": "Usuario no encontrado"}

	usuario.password = make_password(payload.new_password)
	usuario.save(update_fields=["password"])
	return {"message": "Contraseña reseteada por superadmin"}


@usuario_router.post("/logout/", response={200: dict, 401: ErrorSchema})
def logout(request: HttpRequest, authorization: str | None = Header(None)):
	user = _get_user_by_token(authorization)
	if not user:
		return 401, {"message": "Token inválido o no proporcionado"}

	user.token = None
	user.save(update_fields=["token"])
	return {"message": "Logout correcto"}

