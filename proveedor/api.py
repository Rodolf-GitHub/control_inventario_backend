from ninja import Router
from proveedor.models import Proveedor
from proveedor.schemas import ProveedorSchema, ProveedorInSchema, ProveedorUpdateSchema
from usuario.permisions import require_manage_providers, _get_user_from_request, get_allowed_tiendas
from core.schemas import ErrorSchema
from tienda.models import Tienda
from ninja.errors import HttpError

proveedor_router = Router(tags=["Proveedores"])
@proveedor_router.get("/listar/{tienda_id}/", response=list[ProveedorSchema])
def listar_proveedores(request, tienda_id: int):
    """
    Lista todos los proveedores de una tienda específica.
    """
    # Filtrar por tiendas permitidas del usuario
    user = _get_user_from_request(request)
    allowed = get_allowed_tiendas(user)
    if allowed is not None and tienda_id not in allowed:
        return []
    proveedores = Proveedor.objects.filter(tienda_id=tienda_id)
    return proveedores

@proveedor_router.post("/crear/", response={200: ProveedorSchema, 400: ErrorSchema})
@require_manage_providers()
def crear_proveedor(request, proveedor_in: ProveedorInSchema):
    """
    Crea un nuevo proveedor asociado a una tienda.
    """
    tienda = Tienda.objects.get(id=proveedor_in.tienda_id)
    # Validación: nombre de proveedor único por tienda
    if Proveedor.objects.filter(tienda_id=proveedor_in.tienda_id, nombre=proveedor_in.nombre).exists():
        return 400, {"message": "Ya existe un proveedor con ese nombre en la tienda indicada."}

    proveedor = Proveedor.objects.create(
        nombre=proveedor_in.nombre,
        tienda=tienda
    )
    return proveedor

@proveedor_router.patch("/actualizar/{proveedor_id}/", response=ProveedorSchema)
@require_manage_providers()
def actualizar_proveedor(request, proveedor_id: int, proveedor_in: ProveedorUpdateSchema):
    """
    Actualiza un proveedor existente.
    """
    proveedor = Proveedor.objects.get(id=proveedor_id)
    if proveedor_in.nombre:
        proveedor.nombre = proveedor_in.nombre
    proveedor.save()
    return proveedor

@proveedor_router.delete("/eliminar/{proveedor_id}/")
@require_manage_providers()
def eliminar_proveedor(request, proveedor_id: int):
    """
    Elimina un proveedor existente.
    """
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.delete()
    return {"mensaje": "Proveedor eliminado correctamente."}