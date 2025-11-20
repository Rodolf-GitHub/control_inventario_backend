from ninja import Router
from tienda.models import Tienda
from tienda.schemas import TiendaSchema, TiendaInSchema
from core.schemas import ErrorSchema
from ninja.errors import HttpError
from usuario.permisions import require_superadmin, _get_user_from_request, get_allowed_tiendas

tienda_router = Router(tags=["Tiendas"])


@tienda_router.get("/listar/", response=list[TiendaSchema])
def listar_tiendas(request):
    """
    Lista todas las tiendas disponibles.
    """
    # Listado filtrado por tiendas permitidas
    user = _get_user_from_request(request)
    allowed = get_allowed_tiendas(user)
    if allowed is None:
        tiendas = Tienda.objects.all()
    else:
        tiendas = Tienda.objects.filter(id__in=allowed)
    return tiendas
@tienda_router.post("/crear/", response={200: TiendaSchema, 400: ErrorSchema})
@require_superadmin()
def crear_tienda(request, tienda_in: TiendaInSchema):
    """
    Crea una nueva tienda.
    """
    # Validación: nombre único de tienda
    if Tienda.objects.filter(nombre=tienda_in.nombre).exists():
        return 400, {"message": "Ya existe una tienda con ese nombre."}
    tienda = Tienda.objects.create(**tienda_in.dict())
    return tienda
@tienda_router.patch("/actualizar/{tienda_id}/", response=TiendaSchema)
@require_superadmin()
def actualizar_tienda(request, tienda_id: int, tienda_in: TiendaInSchema):
    """
    Actualiza una tienda existente.
    """
    tienda = Tienda.objects.get(id=tienda_id)
    for attr, value in tienda_in.dict().items():
        setattr(tienda, attr, value)
    tienda.save()
    return tienda
@tienda_router.delete("/eliminar/{tienda_id}/")
@require_superadmin()
def eliminar_tienda(request, tienda_id: int):
    """
    Elimina una tienda existente.
    """
    tienda = Tienda.objects.get(id=tienda_id)
    tienda.delete()
    return {"mensaje": "Tienda eliminada correctamente."}