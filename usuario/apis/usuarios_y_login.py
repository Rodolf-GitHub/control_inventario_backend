from ninja import Router
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

usuario_router = Router(tags=["Usuarios y Login"])


def _get_superadmin_from_request(request):
	user = getattr(request, "auth", None)
	if not user:
		return None
	return user if getattr(user, "es_superusuario", False) else None


def _get_user_from_request(request):
	return getattr(request, "auth", None)

@usuario_router.get('/listar/', response={200: list[UserOutSchema], 401: ErrorSchema})
def listar_usuarios(request: HttpRequest):
	admin = _get_superadmin_from_request(request)
	if not admin:
		return 401, {"message": "Se requiere superadmin"}

	usuarios = Usuario.objects.all()
	return list(usuarios)


@usuario_router.post("/login/", response={200: TokenSchema, 400: ErrorSchema},auth=None)
def login(request: HttpRequest, payload: LoginSchema):
	user = Usuario.objects.filter(username=payload.username).first()
	if not user or not check_password(payload.password, user.password):
		return 400, {"message": "Credenciales inválidas"}
	token = uuid.uuid4().hex
	user.token = token
	user.save(update_fields=["token"])
	# Devolver la instancia ORM para que el `TokenSchema` (ModelSchema) la serialice correctamente
	return user


@usuario_router.post("/crear/", response={200: UserOutSchema, 401: ErrorSchema, 400: ErrorSchema})
def crear_usuario(request: HttpRequest, payload: UserCreateSchema):
	admin = _get_superadmin_from_request(request)
	if not admin:
		return 401, {"message": "Se requiere superadmin"}

	if Usuario.objects.filter(username=payload.username).exists():
		return 400, {"message": "El nombre de usuario ya existe"}

	usuario = Usuario(
		username=payload.username,
		password=make_password(payload.password),
		es_superusuario=False,
	)
	usuario.save()

	# opcional: incluir permisos relacionados si el ModelSchema los resuelve
	return usuario



@usuario_router.put("/password/change/", response={200: dict, 401: ErrorSchema, 400: ErrorSchema})
def change_password(request: HttpRequest, payload: ChangePasswordSchema):
	user = _get_user_from_request(request)
	if not user:
		return 401, {"message": "Token inválido o no proporcionado"}

	if not check_password(payload.old_password, user.password):
		return 400, {"message": "Contraseña antigua incorrecta"}

	user.password = make_password(payload.new_password)
	user.save(update_fields=["password"])
	return {"message": "Contraseña actualizada"}


@usuario_router.post("/password/reset/{usuario_id}/", response={200: dict, 401: ErrorSchema, 404: ErrorSchema})
def super_reset_password(request: HttpRequest, usuario_id: int, payload: SuperUserResetPasswordSchema):
	admin = _get_superadmin_from_request(request)
	if not admin:
		return 401, {"message": "Se requiere superadmin"}

	usuario = Usuario.objects.filter(id=usuario_id).first()
	if not usuario:
		return 404, {"message": "Usuario no encontrado"}

	usuario.password = make_password(payload.new_password)
	usuario.save(update_fields=["password"])
	return {"message": "Contraseña reseteada por superadmin"}


@usuario_router.post("/logout/", response={200: dict, 401: ErrorSchema})
def logout(request: HttpRequest):
	user = _get_user_from_request(request)
	if not user:
		return 401, {"message": "Token inválido o no proporcionado"}

	user.token = None
	user.save(update_fields=["token"])
	return {"message": "Logout correcto"}

@usuario_router.delete("/eliminar/{usuario_id}/", response={200: dict, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
def eliminar_usuario(request: HttpRequest, usuario_id: int):
	admin = _get_superadmin_from_request(request)
	if not admin:
		return 401, {"message": "Se requiere superadmin"}

	usuario = Usuario.objects.filter(id=usuario_id).first()
	if not usuario:
		return 404, {"message": "Usuario no encontrado"}

	if getattr(usuario, "es_superusuario", False):
		return 403, {"message": "No se puede eliminar un superusuario"}

	usuario.delete()
	return {"message": "Usuario eliminado correctamente"}
