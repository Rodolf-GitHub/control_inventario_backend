from ninja import Router
from producto.schemas import ProductoSchema, ProductoInSchema, ProductoUpdateSchema
from producto.models import Producto

producto_router = Router(tags=["Productos"])
@producto_router.get("/listar/{proveedor_id}/", response=list[ProductoSchema])
def listar_productos(request, proveedor_id: int):
    """
    Lista todos los productos de un proveedor específico.
    """
    productos = Producto.objects.filter(proveedor_id=proveedor_id)
    return productos
@producto_router.post("/crear/", response=ProductoSchema)
def crear_producto(request, producto_in: ProductoInSchema):
    """
    Crea un nuevo producto asociado a un proveedor.
    """
    producto = Producto.objects.create(
        nombre=producto_in.nombre,
        proveedor_id=producto_in.proveedor_id
    )
    return producto
@producto_router.patch("/actualizar/{producto_id}/", response=ProductoSchema)
def actualizar_producto(request, producto_id: int, producto_in: ProductoUpdateSchema):
    """
    Actualiza un producto existente.
    """
    producto = Producto.objects.get(id=producto_id)
    if producto_in.nombre:
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