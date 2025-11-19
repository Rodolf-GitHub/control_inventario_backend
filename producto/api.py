from ninja import Router
from producto.schemas import ProductoSchema, ProductoInSchema, ProductoUpdateSchema
from core.schemas import ErrorSchema
from producto.models import Producto
from ninja.errors import HttpError
from django.db import IntegrityError

producto_router = Router(tags=["Productos"])
@producto_router.get("/listar/{proveedor_id}/", response=list[ProductoSchema])
def listar_productos(request, proveedor_id: int):
    """
    Lista todos los productos de un proveedor específico.
    """
    productos = Producto.objects.filter(proveedor_id=proveedor_id)
    return productos
@producto_router.post("/crear/", response={200: ProductoSchema, 400: ErrorSchema})
def crear_producto(request, producto_in: ProductoInSchema):
    """
    Crea un nuevo producto asociado a un proveedor.
    """
    # Validación: nombre único por proveedor
    if Producto.objects.filter(proveedor_id=producto_in.proveedor_id, nombre=producto_in.nombre).exists():
        return 400, {"message": "Ya existe un producto con ese nombre para este proveedor."}
    try:
        producto = Producto.objects.create(
            nombre=producto_in.nombre,
            proveedor_id=producto_in.proveedor_id
        )
    except IntegrityError:
        return 400, {"message": "Ya existe un producto con ese nombre para este proveedor (constraint)."}
    return producto
@producto_router.patch("/actualizar/{producto_id}/", response={200: ProductoSchema, 400: ErrorSchema})
def actualizar_producto(request, producto_id: int, producto_in: ProductoUpdateSchema):
    """
    Actualiza un producto existente.
    """
    producto = Producto.objects.get(id=producto_id)
    if producto_in.nombre:
        # comprobar duplicado en el mismo proveedor
        if Producto.objects.filter(proveedor_id=producto.proveedor_id, nombre=producto_in.nombre).exclude(id=producto_id).exists():
            return 400, {"message": "Ya existe un producto con ese nombre para este proveedor."}
        producto.nombre = producto_in.nombre
    producto.save()
    return producto
@producto_router.delete("/eliminar/{producto_id}/")
def eliminar_producto(request, producto_id: int):
    """
    Elimina un producto existente.
    """
    producto = Producto.objects.get(id=producto_id)
    producto.delete()
    return {"mensaje": "Producto eliminado correctamente."}