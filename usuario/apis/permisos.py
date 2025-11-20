from ninja import Router
from django.http import HttpRequest

from usuario.models import Usuario, PermisosUsuarioTienda
from tienda.models import Tienda
from usuario.schemas.permisosSchema import (
	PermisosUsuarioTiendaSchema,
	PermisosUsuarioTiendaInSchema,
	PermisosUsuarioTiendaUpdateSchema,
)
from core.schemas import ErrorSchema
from usuario.permisions import require_superadmin

permisos_router = Router(tags=["Permisos Usuario-Tienda"])


@permisos_router.get("/usuario/{usuario_id}/", response={200: list[PermisosUsuarioTiendaSchema], 401: ErrorSchema})
@require_superadmin()
def listar_permisos(request: HttpRequest, usuario_id: int):
	permisos = PermisosUsuarioTienda.objects.filter(usuario_id=usuario_id)
	return list(permisos)


@permisos_router.post("crear/", response={200: PermisosUsuarioTiendaSchema, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema})
@require_superadmin()
def crear_permiso(request: HttpRequest, payload: PermisosUsuarioTiendaInSchema):
	# Obtener usuario_id desde el payload (convención esperada).
	usuario_id = getattr(payload, "usuario_id", None)

	# Si por alguna razón no se envió usuario_id, devolver 400 para indicar payload inválido
	if not usuario_id:
		return 400, {"message": "Incluye 'usuario_id' en el payload"}

	if not Usuario.objects.filter(id=usuario_id).exists():
		return 400, {"message": "Usuario no encontrado"}

	if not Tienda.objects.filter(id=payload.tienda_id).exists():
		return 400, {"message": "Tienda no encontrada"}

	# No permitir crear permisos para superusuarios
	if Usuario.objects.filter(id=usuario_id, es_superusuario=True).exists():
		return 403, {"message": "No se pueden asignar permisos a un superusuario"}

	# evitar duplicados según constraint
	if PermisosUsuarioTienda.objects.filter(usuario_id=usuario_id, tienda_id=payload.tienda_id).exists():
		return 400, {"message": "Ya existen permisos para ese usuario en la tienda indicada"}

	permiso = PermisosUsuarioTienda.objects.create(
		usuario_id=usuario_id,
		tienda_id=payload.tienda_id,
		puede_gestionar_proveedores=payload.puede_gestionar_proveedores,
		puede_gestionar_productos=payload.puede_gestionar_productos,
		puede_gestionar_compras=payload.puede_gestionar_compras,
		puede_editar_compras=payload.puede_editar_compras,
		puede_ver_inventario_compras=payload.puede_ver_inventario_compras,
	)

	return permiso


@permisos_router.put("actualizar/{permiso_id}/", response={200: PermisosUsuarioTiendaSchema, 401: ErrorSchema, 404: ErrorSchema})
@require_superadmin()
def actualizar_permiso(request: HttpRequest, permiso_id: int, payload: PermisosUsuarioTiendaUpdateSchema):

	permiso = PermisosUsuarioTienda.objects.filter(id=permiso_id).first()
	if not permiso:
		return 404, {"message": "Permiso no encontrado"}

	permiso.puede_gestionar_proveedores = payload.puede_gestionar_proveedores
	permiso.puede_gestionar_productos = payload.puede_gestionar_productos
	permiso.puede_gestionar_compras = payload.puede_gestionar_compras
	permiso.puede_editar_compras = payload.puede_editar_compras
	permiso.puede_ver_inventario_compras = payload.puede_ver_inventario_compras
	permiso.save()
	return permiso


@permisos_router.delete("eliminar/{permiso_id}/", response={200: dict, 401: ErrorSchema, 404: ErrorSchema})
@require_superadmin()
def eliminar_permiso(request: HttpRequest, permiso_id: int):

	permiso = PermisosUsuarioTienda.objects.filter(id=permiso_id).first()
	if not permiso:
		return 404, {"message": "Permiso no encontrado"}

	permiso.delete()
	return {"message": "Permiso eliminado"}

