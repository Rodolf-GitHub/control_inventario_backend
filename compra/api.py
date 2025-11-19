from ninja import Router
from compra.schemas import (
    CompraSchema,
    CompraInSchema,
    DetalleCompraSchema,
    DetalleCompraInSchema,
    DetalleCompraUpdateSchema,
    CompraWithDetailsSchema,
    CompraUpdateSchema
)
from compra.models import Compra, DetalleCompra
from proveedor.models import Proveedor
from producto.models import Producto
from django.db.models import Sum, Prefetch
from datetime import date
from typing import Optional
from ninja.errors import HttpError

compra_router = Router(tags=["Compras"])


def _detalle_to_dict(detalle: DetalleCompra) -> dict:
    return {
        "id": detalle.id,
        "compra_id": detalle.compra_id,
        "producto_id": detalle.producto_id,
        "cantidad": detalle.cantidad,
        "inventario_anterior": detalle.inventario_anterior,
        "producto_nombre": detalle.producto.nombre if detalle.producto else None,
    }


def _compra_to_dict(compra: Compra, detalles_list: list[DetalleCompra]) -> dict:
    return {
        "id": compra.id,
        "proveedor_id": compra.proveedor_id,
        "fecha_compra": compra.fecha_compra,
        "detalles": [_detalle_to_dict(d) for d in detalles_list],
    }

@compra_router.get("/rango/{proveedor_id}/", response=list[CompraWithDetailsSchema])
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
        raise HttpError(404, "Proveedor no encontrado")

    # Filtrar por proveedor recibido en la ruta
    qs = Compra.objects.filter(proveedor__id=proveedor_id)
    if fecha_inicio and fecha_fin:
        qs = qs.filter(fecha_compra__range=(fecha_inicio, fecha_fin))

    # Prefetch detalles con su producto para que el ModelSchema pueda resolver producto.nombre
    qs = qs.prefetch_related(
        Prefetch("detalles", queryset=DetalleCompra.objects.select_related("producto"))
    )

    ordering = "fecha_compra" if (str(order).lower() != "desc") else "-fecha_compra"
    compras = list(qs.order_by(ordering)[:limit])
    return compras



@compra_router.post("/crear/", response=CompraWithDetailsSchema)
def crear_compra(request, compra_in: CompraInSchema):
    """Crea una nueva compra y genera un detalle por cada producto del proveedor con valores en 0."""
    # Validación: no permitir más de una compra en la misma fecha para el mismo proveedor
    if Compra.objects.filter(proveedor_id=compra_in.proveedor_id, fecha_compra=compra_in.fecha_compra).exists():
        raise HttpError(400, "Ya existe una compra para este proveedor en la fecha indicada.")

    compra = Compra.objects.create(**compra_in.dict())

    # Obtener el proveedor de la compra y filtrar productos por esa instancia
    proveedor_obj = compra.proveedor
    productos = Producto.objects.filter(proveedor=proveedor_obj)
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
            Prefetch("detalles", queryset=DetalleCompra.objects.select_related("producto"))
        ).get(id=compra.id)
    )
    return compra_con_detalles

@compra_router.post("/detalle/crear/{compra_id}/", response=DetalleCompraSchema)
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
    return DetalleCompra.objects.select_related("producto").get(id=detalle.id)


@compra_router.patch("/detalle/editar/{detalle_id}/", response=DetalleCompraSchema)
def editar_detalle(request, detalle_id: int, detalle_in: DetalleCompraUpdateSchema):
    """Edita un detalle de compra existente."""
    detalle = DetalleCompra.objects.select_related("producto").get(id=detalle_id)
    # Actualizar solo los campos permitidos
    detalle.cantidad = detalle_in.cantidad
    detalle.inventario_anterior = detalle_in.inventario_anterior
    detalle.save()
    return DetalleCompra.objects.select_related("producto").get(id=detalle.id)

@compra_router.patch("/compra//{compra}/", response=CompraSchema)
def actualizar_compra(request, compra: int, compra_in: CompraUpdateSchema):
    """Actualiza una compra existente."""
    compra_obj = Compra.objects.get(id=compra)
    if compra_in.fecha_compra:
        compra_obj.fecha_compra = compra_in.fecha_compra
    compra_obj.save()
    return compra_obj

@compra_router.delete("/detalle/eliminar/{detalle_id}/")
def eliminar_detalle(request, detalle_id: int):
    """Elimina un detalle de compra existente."""
    detalle = DetalleCompra.objects.get(id=detalle_id)
    detalle.delete()
    return {"mensaje": "Detalle de compra eliminado correctamente."}


@compra_router.delete("/eliminar/{compra_id}/")
def eliminar_compra(request, compra_id: int):
    """Elimina una compra (y sus detalles por cascade)."""
    compra = Compra.objects.get(id=compra_id)
    compra.delete()
    return {"mensaje": "Compra eliminada correctamente."}
