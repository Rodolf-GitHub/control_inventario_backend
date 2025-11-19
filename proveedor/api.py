from ninja import Router
from proveedor.models import Proveedor
from proveedor.schemas import ProveedorSchema, ProveedorInSchema, ProveedorUpdateSchema
from tienda.models import Tienda

proveedor_router = Router(tags=["Proveedores"])
@proveedor_router.get("/listar/{tienda_id}/", response=list[ProveedorSchema])
def listar_proveedores(request, tienda_id: int):
    """
    Lista todos los proveedores de una tienda específica.
    """
    proveedores = Proveedor.objects.filter(tienda_id=tienda_id)
    return proveedores

@proveedor_router.post("/crear/", response=ProveedorSchema)
def crear_proveedor(request, proveedor_in: ProveedorInSchema):
    """
    Crea un nuevo proveedor asociado a una tienda.
    """
    tienda = Tienda.objects.get(id=proveedor_in.tienda_id)
    proveedor = Proveedor.objects.create(
        nombre=proveedor_in.nombre,
        tienda=tienda
    )
    return proveedor

@proveedor_router.patch("/actualizar/{proveedor_id}/", response=ProveedorSchema)
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
def eliminar_proveedor(request, proveedor_id: int):
    """
    Elimina un proveedor existente.
    """
    proveedor = Proveedor.objects.get(id=proveedor_id)
    proveedor.delete()
    return {"mensaje": "Proveedor eliminado correctamente."}