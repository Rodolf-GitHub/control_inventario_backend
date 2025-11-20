from ninja import Router, Header
from django.http import HttpRequest

from usuario.models import Usuario, PermisosUsuarioTienda
from tienda.models import Tienda
from usuario.schemas.permisosSchema import (
	PermisosUsuarioTiendaSchema,
	PermisosUsuarioTiendaInSchema,
	PermisosUsuarioTiendaUpdateSchema,
)
from core.schemas import ErrorSchema

permisos_router = Router()


def _get_superadmin_by_token(raw_auth: str | None):
	if not raw_auth:
		return None
	token = raw_auth.strip()
	if token.lower().startswith("token "):
		token = token.split(" ", 1)[1].strip()
	return Usuario.objects.filter(token=token, es_superusuario=True).first()


@permisos_router.get("/usuario/{usuario_id}/", response={200: list[PermisosUsuarioTiendaSchema], 401: ErrorSchema})
def listar_permisos(request: HttpRequest, usuario_id: int, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	permisos = PermisosUsuarioTienda.objects.filter(usuario_id=usuario_id)
	return list(permisos)


@permisos_router.post("/", response={200: PermisosUsuarioTiendaSchema, 400: ErrorSchema, 401: ErrorSchema})
def crear_permiso(request: HttpRequest, payload: PermisosUsuarioTiendaInSchema, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	if not Usuario.objects.filter(id=request.json().get('usuario_id')):
		# el usuario se pasa por payload.usuario_id en la convención anterior; algunos clientes lo pasarán en body
		pass

	if not Usuario.objects.filter(id=payload.__dict__.get('usuario_id')):
		# si no existe, retornamos error
		return 400, {"message": "Usuario no encontrado. Incluye 'usuario_id' en el payload"}

	if not Tienda.objects.filter(id=payload.tienda_id).exists():
		return 400, {"message": "Tienda no encontrada"}

	# evitar duplicados según constraint
	if PermisosUsuarioTienda.objects.filter(usuario_id=payload.__dict__.get('usuario_id'), tienda_id=payload.tienda_id).exists():
		return 400, {"message": "Ya existen permisos para ese usuario en la tienda indicada"}

	permiso = PermisosUsuarioTienda.objects.create(
		usuario_id=payload.__dict__.get('usuario_id'),
		tienda_id=payload.tienda_id,
		puede_gestionar_proveedores=payload.puede_gestionar_proveedores,
		puede_gestionar_productos=payload.puede_gestionar_productos,
		puede_gestionar_compras=payload.puede_gestionar_compras,
		puede_ver_inventario_compras=payload.puede_ver_inventario_compras,
	)

	return permiso


@permisos_router.put("/{permiso_id}/", response={200: PermisosUsuarioTiendaSchema, 401: ErrorSchema, 404: ErrorSchema})
def actualizar_permiso(request: HttpRequest, permiso_id: int, payload: PermisosUsuarioTiendaUpdateSchema, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	permiso = PermisosUsuarioTienda.objects.filter(id=permiso_id).first()
	if not permiso:
		return 404, {"message": "Permiso no encontrado"}

	permiso.puede_gestionar_proveedores = payload.puede_gestionar_proveedores
	permiso.puede_gestionar_productos = payload.puede_gestionar_productos
	permiso.puede_gestionar_compras = payload.puede_gestionar_compras
	permiso.puede_ver_inventario_compras = payload.puede_ver_inventario_compras
	permiso.save()
	return permiso


@permisos_router.delete("/{permiso_id}/", response={200: dict, 401: ErrorSchema, 404: ErrorSchema})
def eliminar_permiso(request: HttpRequest, permiso_id: int, authorization: str | None = Header(None)):
	admin = _get_superadmin_by_token(authorization)
	if not admin:
		return 401, {"message": "Token de superadmin inválido o no proporcionado"}

	permiso = PermisosUsuarioTienda.objects.filter(id=permiso_id).first()
	if not permiso:
		return 404, {"message": "Permiso no encontrado"}

	permiso.delete()
	return {"message": "Permiso eliminado"}

