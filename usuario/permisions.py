from functools import wraps
import json
from django.http import HttpRequest
from usuario.models import Usuario, PermisosUsuarioTienda


def _get_user_from_request(request: HttpRequest) -> Usuario | None:
	# Si Ninja o algún middleware ya puso request.auth (AuthBearer), úsalo
	user = getattr(request, "auth", None)
	if user:
		return user

	# Intentar extraer token del header Authorization
	auth = request.META.get("HTTP_AUTHORIZATION", "")
	if not auth:
		return None
	parts = auth.split()
	if len(parts) == 2 and parts[0].lower() == "bearer":
		token = parts[1]
	else:
		token = auth.strip()

	return Usuario.objects.filter(token=token).first()


def has_permission(user: Usuario, tienda_id: int, perm_attr: str) -> bool:
	"""Comprueba si `user` tiene el permiso `perm_attr` para la `tienda_id`.

	Si `user.es_superusuario` devuelve True.
	"""
	if not user:
		return False
	if getattr(user, "es_superusuario", False):
		return True
	permiso = PermisosUsuarioTienda.objects.filter(usuario=user, tienda_id=tienda_id).first()
	if not permiso:
		return False
	return bool(getattr(permiso, perm_attr, False))


def _extract_tienda_id(request: HttpRequest, kwargs: dict, tienda_kw: str = "tienda_id") -> int | None:
	# 1) buscar en kwargs (ruta)
	if tienda_kw in kwargs:
		return kwargs[tienda_kw]
	# 2) buscar en query params
	try:
		val = request.GET.get(tienda_kw)
		if val:
			return int(val)
	except Exception:
		pass
	# 3) intentar leer body JSON (POST/PUT)
	try:
		if request.body:
			data = json.loads(request.body)
			if isinstance(data, dict) and tienda_kw in data:
				return int(data[tienda_kw])
	except Exception:
		pass
	return None


def require_permission(perm_attr: str, tienda_kw: str = "tienda_id"):
	"""Decorador que exige que el usuario tenga `perm_attr` en la tienda indicada.

	Uso:
	  @require_permission('puede_gestionar_productos')
	  def view(request, tienda_id, ...):
		  ...
	"""

	def decorator(func):
		@wraps(func)
		def wrapper(request: HttpRequest, *args, **kwargs):
			user = _get_user_from_request(request)
			if not user:
				return 401, {"message": "Token inválido o no proporcionado"}

			tienda_id = _extract_tienda_id(request, kwargs, tienda_kw)
			if tienda_id is None:
				return 400, {"message": f"Falta '{tienda_kw}' (ruta, query o body)"}

			if not has_permission(user, tienda_id, perm_attr):
				return 403, {"message": "No autorizado para esta operación"}

			return func(request, *args, **kwargs)

		return wrapper

	return decorator


# Decoradores específicos para conveniencia
def require_manage_products(tienda_kw: str = "tienda_id"):
	return require_permission("puede_gestionar_productos", tienda_kw)


def require_manage_providers(tienda_kw: str = "tienda_id"):
	return require_permission("puede_gestionar_proveedores", tienda_kw)


def require_manage_purchases(tienda_kw: str = "tienda_id"):
	return require_permission("puede_gestionar_compras", tienda_kw)


def require_view_inventory(tienda_kw: str = "tienda_id"):
	return require_permission("puede_ver_inventario_compras", tienda_kw)

