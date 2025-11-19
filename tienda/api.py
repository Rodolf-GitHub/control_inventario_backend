from ninja import Router
from tienda.models import Tienda
from tienda.schemas import TiendaSchema, TiendaInSchema
from core.schemas import ErrorSchema
from ninja.errors import HttpError

tienda_router = Router(tags=["Tiendas"])

@tienda_router.get("/listar/", response=list[TiendaSchema])
def listar_tiendas(request):
    """
    Lista todas las tiendas disponibles.
    """
    tiendas = Tienda.objects.all()
    return tiendas
@tienda_router.post("/crear/", response={200: TiendaSchema, 400: ErrorSchema})
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
def eliminar_tienda(request, tienda_id: int):
    """
    Elimina una tienda existente.
    """
    tienda = Tienda.objects.get(id=tienda_id)
    tienda.delete()
    return {"mensaje": "Tienda eliminada correctamente."}