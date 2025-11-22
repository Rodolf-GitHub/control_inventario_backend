from ninja import Router
from usuario.permisions import require_manage_purchases, _get_user_from_request, get_allowed_tiendas, require_edit_purchases, has_permission
from compra.schemas import (
    CompraSchema,
    CompraInSchema,
    DetalleCompraSchema,
    DetalleCompraInSchema,
    DetalleCompraUpdateSchema,
    CompraWithDetailsSchema,
    CompraUpdateSchema,
)
from core.schemas import ErrorSchema
from compra.models import Compra, DetalleCompra
from proveedor.models import Proveedor
from producto.models import Producto
from django.db.models import Sum, Prefetch
from datetime import date
from typing import Optional
from ninja.errors import HttpError
import logging

logger = logging.getLogger(__name__)
# Límite superior aceptable para cantidades e inventarios (evita overflow en SQLite)
MAX_ALLOWED = 10 ** 9

compra_router = Router(tags=["Compras"])


def _detalle_to_dict(detalle: DetalleCompra, request) -> dict:
    # Decidir visibilidad de inventario a partir del request y la tienda asociada
    tienda_id = None
    try:
        tienda_id = detalle.compra.proveedor.tienda_id
    except Exception:
        tienda_id = detalle.compra.proveedor.tienda_id if hasattr(detalle, 'compra') and hasattr(detalle.compra, 'proveedor') else None
    show_inventario = False
    user = _get_user_from_request(request)
    if tienda_id is not None:
        show_inventario = has_permission(user, tienda_id, "puede_ver_inventario_compras")
    # Resolver nombre de producto robustamente (en caso de que no esté cargado por select_related)
    producto_nombre = None
    try:
        producto_nombre = detalle.producto.nombre if getattr(detalle, 'producto', None) else None
    except Exception:
        producto_nombre = None
    if not producto_nombre:
        try:
            producto_obj = Producto.objects.get(id=detalle.producto_id)
            producto_nombre = getattr(producto_obj, 'nombre', None)
        except Exception:
            producto_nombre = None

    return {
        "id": detalle.id,
        "compra_id": detalle.compra_id,
        "producto_id": detalle.producto_id,
        "cantidad": detalle.cantidad,
            # si no puede ver inventario, devolver el marcador '?'
            "inventario_anterior": detalle.inventario_anterior if show_inventario else "?",
        "producto_nombre": producto_nombre,
    }


def _compra_to_dict(compra: Compra, detalles_list: list[DetalleCompra], request) -> dict:
    return {
        "id": compra.id,
        "proveedor_id": compra.proveedor_id,
        "fecha_compra": compra.fecha_compra,
        "detalles": [_detalle_to_dict(d, request) for d in detalles_list],
    }

@compra_router.get("/rango/{proveedor_id}/", response={200: list[CompraWithDetailsSchema], 400: ErrorSchema, 404: ErrorSchema})
def compras_por_rango(
    request,
    proveedor_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    limit: int = 3,
    order: str = "asc",
):
    """Devuelve hasta `limit` compras con detalles.

    - Si no se pasa `fecha_inicio` ni `fecha_fin`, devuelve las últimas `limit` compras.
    - Si se pasa un rango (`fecha_inicio` y `fecha_fin`), devuelve las últimas `limit` compras dentro de ese rango.
    - Parámetro `order`: `asc` para ascendente (fecha antigua->nueva), `desc` para descendente (por defecto).
    """
    # Validar que el proveedor exista
    if not Proveedor.objects.filter(id=proveedor_id).exists():
        return 404, {"message": "Proveedor no encontrado"}

    # Verificar acceso del usuario a la tienda de ese proveedor (GETs libres pero filtradas)
    user = _get_user_from_request(request)
    allowed = get_allowed_tiendas(user)
    proveedor_obj = Proveedor.objects.get(id=proveedor_id)
    if allowed is not None and proveedor_obj.tienda_id not in allowed:
        return []

    # Filtrar por proveedor recibido en la ruta
    qs = Compra.objects.filter(proveedor__id=proveedor_id)
    if fecha_inicio and fecha_fin:
        qs = qs.filter(fecha_compra__range=(fecha_inicio, fecha_fin))

    # Prefetch detalles con su producto para que el ModelSchema pueda resolver producto.nombre
    # y ordenar los detalles según el `orden` del producto
    qs = qs.prefetch_related(
        Prefetch("detalles", queryset=DetalleCompra.objects.select_related("producto").order_by("producto__orden"))
    )

    ordering = "fecha_compra" if (str(order).lower() != "desc") else "-fecha_compra"
    compras = list(qs.order_by(ordering)[:limit])
    # convertir a dicts: la visibilidad del inventario se decidirá dentro de los helpers con el request
    result = [_compra_to_dict(c, list(c.detalles.all()), request) for c in compras]
    return result



@compra_router.post("/crear/", response={200: CompraWithDetailsSchema, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema})
@require_manage_purchases()
def crear_compra(request, compra_in: CompraInSchema):
    """Crea una nueva compra y genera un detalle por cada producto del proveedor con valores en 0."""
    # Validación: no permitir más de una compra en la misma fecha para el mismo proveedor
    if Compra.objects.filter(proveedor_id=compra_in.proveedor_id, fecha_compra=compra_in.fecha_compra).exists():
        return 400, {"message": "Ya existe una compra para este proveedor en la fecha indicada."}

    compra = Compra.objects.create(**compra_in.dict())

    # Obtener el proveedor de la compra y filtrar productos por esa instancia
    proveedor_obj = compra.proveedor
    # asegurar orden por `orden` del producto al crear detalles
    productos = Producto.objects.filter(proveedor=proveedor_obj).order_by("orden")
    detalles_creados = []
    for producto in productos:
        cantidad_compra = 0
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=producto,
            cantidad=cantidad_compra,
            inventario_anterior=0,
        )
        detalles_creados.append(detalle)

    # Devolver la instancia ORM con los detalles precargados para que el schema pueda resolver nombres
    compra_con_detalles = (
        Compra.objects.prefetch_related(
            Prefetch("detalles", queryset=DetalleCompra.objects.select_related("producto").order_by("producto__orden"))
        ).get(id=compra.id)
    )
    return _compra_to_dict(compra_con_detalles, list(compra_con_detalles.detalles.all()), request)


@compra_router.post("/detalle/crear/{compra_id}/", response={200: DetalleCompraSchema, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema})
@require_manage_purchases()
def crear_detalle(request, compra_id: int, detalle_in: DetalleCompraInSchema):
    """Crea un nuevo detalle de compra para una compra existente."""
    compra = Compra.objects.get(id=compra_id)
    producto = Producto.objects.get(id=detalle_in.producto_id)
    detalle = DetalleCompra.objects.create(
        compra=compra,
        producto=producto,
        cantidad=detalle_in.cantidad,
        inventario_anterior=detalle_in.inventario_anterior,
    )
    detalle_obj = DetalleCompra.objects.select_related("producto", "compra__proveedor").get(id=detalle.id)
    return _detalle_to_dict(detalle_obj, request)


@compra_router.patch("/detalle/editar/{detalle_id}/", response={200: DetalleCompraSchema, 400: ErrorSchema, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
@require_edit_purchases()
def editar_detalle(request, detalle_id: int, detalle_in: DetalleCompraUpdateSchema):
    """Edita un detalle de compra existente."""
    detalle = DetalleCompra.objects.select_related("producto", "compra__proveedor").get(id=detalle_id)
    # Aplicar sólo los campos realmente presentes en el JSON del request (PATCH parcial)
    import json
    try:
        body_data = json.loads(request.body) if request.body else {}
    except Exception:
        body_data = {}

    updated = False

    def _coerce_int(val, default=0):
        # Acepta int, str numérica, float; valores vacíos o None devuelven default
        if val is None:
            return default
        if isinstance(val, int):
            return val
        try:
            # strings: strip and try int, then float
            if isinstance(val, str):
                s = val.strip()
                if s == "":
                    return default
                return int(s)
            # floats
            if isinstance(val, float):
                return int(val)
            # other types fallback
            return int(val)
        except Exception:
            return default

    # Si el cliente envió 'cantidad' lo aplicamos coercionado
    if "cantidad" in body_data:
        raw = body_data.get("cantidad")
        coerced = _coerce_int(raw, default=0)
        if coerced < 0:
            logger.warning("editar_detalle: cantidad negativa recibida (%r) para detalle_id=%s — ajustando a 0", raw, detalle_id)
            coerced = 0
        if coerced > MAX_ALLOWED:
            logger.warning("editar_detalle: cantidad excesiva recibida (%r) para detalle_id=%s — limitando a %s", raw, detalle_id, MAX_ALLOWED)
            coerced = MAX_ALLOWED
        logger.debug("editar_detalle: coercing cantidad raw=%r -> %r for detalle_id=%s", raw, coerced, detalle_id)
        detalle.cantidad = coerced
        updated = True

    # Si el cliente envió 'inventario_anterior' lo aplicamos coercionado
    if "inventario_anterior" in body_data:
        raw = body_data.get("inventario_anterior")
        coerced = _coerce_int(raw, default=0)
        if coerced < 0:
            logger.warning("editar_detalle: inventario_anterior negativo recibido (%r) para detalle_id=%s — ajustando a 0", raw, detalle_id)
            coerced = 0
        if coerced > MAX_ALLOWED:
            logger.warning("editar_detalle: inventario_anterior excesivo recibido (%r) para detalle_id=%s — limitando a %s", raw, detalle_id, MAX_ALLOWED)
            coerced = MAX_ALLOWED
        logger.debug("editar_detalle: coercing inventario_anterior raw=%r -> %r for detalle_id=%s", raw, coerced, detalle_id)
        detalle.inventario_anterior = coerced
        updated = True

    if updated:
        try:
            detalle.save()
        except Exception as e:
            logger.exception("Error saving DetalleCompra id=%s with data=%s: %s", detalle_id, body_data, e)
            return 400, {"message": "Error al actualizar detalle"}
    detalle_obj = DetalleCompra.objects.select_related("producto", "compra__proveedor").get(id=detalle.id)
    return _detalle_to_dict(detalle_obj, request)

@compra_router.patch("/compra/{compra}/", response={200: CompraSchema, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
@require_manage_purchases()
def actualizar_compra(request, compra: int, compra_in: CompraUpdateSchema):
    """Actualiza una compra existente."""
    compra_obj = Compra.objects.get(id=compra)
    if compra_in.fecha_compra:
        compra_obj.fecha_compra = compra_in.fecha_compra
    compra_obj.save()
    return compra_obj

@compra_router.delete("/detalle/eliminar/{detalle_id}/", response={200: dict, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
@require_manage_purchases()
def eliminar_detalle(request, detalle_id: int):
    """Elimina un detalle de compra existente."""
    detalle = DetalleCompra.objects.get(id=detalle_id)
    detalle.delete()
    return {"mensaje": "Detalle de compra eliminado correctamente."}


@compra_router.delete("/eliminar/{compra_id}/", response={200: dict, 401: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
@require_manage_purchases()
def eliminar_compra(request, compra_id: int):
    """Elimina una compra (y sus detalles por cascade)."""
    compra = Compra.objects.get(id=compra_id)
    compra.delete()
    return {"mensaje": "Compra eliminada correctamente."}
