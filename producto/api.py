from ninja import Router
from usuario.permisions import require_manage_products, _get_user_from_request, get_allowed_tiendas
from usuario.permisions import has_permission
from producto.schemas import ProductoSchema, ProductoInSchema, ProductoUpdateSchema, MoverProductoSchema
from core.schemas import ErrorSchema
from producto.models import Producto
from proveedor.models import Proveedor
from ninja.errors import HttpError
from django.db import IntegrityError
from django.db.models import Max
from django.db import transaction

producto_router = Router(tags=["Productos"])
@producto_router.get("/listar/{proveedor_id}/", response=list[ProductoSchema])
def listar_productos(request, proveedor_id: int):
    """
    Lista todos los productos de un proveedor específico.
    """
    # Filtrar por tiendas permitidas del usuario (GETs son públicos pero limitados por tiendas)
    user = _get_user_from_request(request)
    allowed = get_allowed_tiendas(user)
    # comprobar proveedor y su tienda
    proveedor = Proveedor.objects.filter(id=proveedor_id).first()
    if not proveedor:
        return []
    tienda_id = proveedor.tienda_id
    if allowed is not None and tienda_id not in allowed:
        return []
    productos = Producto.objects.filter(proveedor_id=proveedor_id).order_by('orden')
    return productos
@producto_router.post("/crear/", response={200: ProductoSchema, 400: ErrorSchema})
@require_manage_products()
def crear_producto(request, producto_in: ProductoInSchema):
    """
    Crea un nuevo producto asociado a un proveedor.
    """
    # Validación: nombre único por proveedor
    if Producto.objects.filter(proveedor_id=producto_in.proveedor_id, nombre=producto_in.nombre).exists():
        return 400, {"message": "Ya existe un producto con ese nombre para este proveedor."}
    try:
        # asignar orden secuencial por proveedor (siempre automático)
        max_orden = Producto.objects.filter(proveedor_id=producto_in.proveedor_id).aggregate(max_ord=Max('orden'))['max_ord']
        next_orden = 1 if max_orden is None else int(max_orden) + 1

        producto = Producto.objects.create(
            nombre=producto_in.nombre,
            proveedor_id=producto_in.proveedor_id,
            orden=next_orden,
        )
    except IntegrityError:
        return 400, {"message": "Ya existe un producto con ese nombre para este proveedor (constraint)."}
    return producto


@producto_router.post("/mover/", response={200: dict, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema})
def mover_producto(request, payload: MoverProductoSchema):
    """Mueve un producto intercambiando su `orden` con el producto de arriba/abajo."""
    try:
        producto = Producto.objects.get(id=payload.producto_id)
    except Producto.DoesNotExist:
        return 400, {"message": "Producto no encontrado"}

    # permiso: verificar que el usuario pueda gestionar productos en la tienda del proveedor
    user = _get_user_from_request(request)
    tienda_id = producto.proveedor.tienda_id
    if not user or not has_permission(user, tienda_id, 'puede_gestionar_productos'):
        return 403, {"message": "No autorizado para mover productos en esta tienda"}

    # Hacer el swap dentro de una transacción para evitar condiciones de carrera
    with transaction.atomic():
        # volver a obtener el producto bloqueándolo
        producto = Producto.objects.select_for_update().get(id=producto.id)

        # Normalizar/reindexar órdenes para este proveedor para evitar duplicados/huecos
        prods_for_provider = list(
            Producto.objects.filter(proveedor_id=producto.proveedor_id).order_by('orden', 'id').select_for_update()
        )
        # Reasignar 1..N en memoria y hacer bulk_update sólo si hubo cambios
        changed = False
        for idx, p in enumerate(prods_for_provider, start=1):
            if p.orden is None or int(p.orden) != idx:
                p.orden = idx
                changed = True
        if changed:
            Producto.objects.bulk_update(prods_for_provider, ['orden'])
            # refrescar la instancia actual después del bulk_update
            producto = Producto.objects.select_for_update().get(id=producto.id)

        if payload.direccion == 'arriba':
            neighbor_qs = Producto.objects.filter(
                proveedor_id=producto.proveedor_id, orden__lt=producto.orden
            ).exclude(id=producto.id).order_by('-orden')
        else:
            neighbor_qs = Producto.objects.filter(
                proveedor_id=producto.proveedor_id, orden__gt=producto.orden
            ).exclude(id=producto.id).order_by('orden')

        # bloquear el vecino también si existe
        neighbor = neighbor_qs.select_for_update().first()

        if not neighbor:
            return 400, {"message": "No hay producto para intercambiar en esa dirección"}

        before = {
            "producto": {"id": producto.id, "orden": producto.orden},
            "neighbor": {"id": neighbor.id, "orden": neighbor.orden},
        }

        # intercambiar ordenes de forma segura
        prod_ord = producto.orden
        producto.orden = neighbor.orden
        neighbor.orden = prod_ord
        producto.save()
        neighbor.save()

        after = {
            "producto": {"id": producto.id, "orden": producto.orden},
            "neighbor": {"id": neighbor.id, "orden": neighbor.orden},
        }

    return {"moved": producto.id, "swapped_with": neighbor.id, "before": before, "after": after}
@producto_router.patch("/actualizar/{producto_id}/", response={200: ProductoSchema, 400: ErrorSchema})
@require_manage_products()
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
@producto_router.delete("/eliminar/{producto_id}/", response={200: dict, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
@require_manage_products()
def eliminar_producto(request, producto_id: int):
    """
    Elimina un producto existente.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return 404, {"message": "Producto no encontrado"}
    try:
        producto.delete()
    except Exception as e:
        return 400, {"message": "Error al eliminar producto"}
    return {"mensaje": "Producto eliminado correctamente."}