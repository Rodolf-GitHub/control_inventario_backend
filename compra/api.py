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
from producto.models import Producto
from django.db.models import Sum
from datetime import date
from typing import Optional

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

@compra_router.get("/rango/", response=list[CompraWithDetailsSchema])
def compras_por_rango(
    request,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    limit: int = 3,
):
    """Devuelve hasta `limit` compras con detalles.

    - Si no se pasa `fecha_inicio` ni `fecha_fin`, devuelve las últimas `limit` compras.
    - Si se pasa un rango (`fecha_inicio` y `fecha_fin`), devuelve las últimas `limit` compras dentro de ese rango.
    """
    qs = Compra.objects.all()
    if fecha_inicio and fecha_fin:
        qs = qs.filter(fecha_compra__range=(fecha_inicio, fecha_fin))

    compras = qs.order_by("-fecha_compra")[:limit]
    resultado = []
    for compra in compras:
        detalles = list(DetalleCompra.objects.filter(compra=compra))
        resultado.append(_compra_to_dict(compra, detalles))
    return resultado



@compra_router.post("/crear/", response=CompraWithDetailsSchema)
def crear_compra(request, compra_in: CompraInSchema):
    """Crea una nueva compra y genera un detalle por cada producto del proveedor con valores en 0."""
    compra = Compra.objects.create(**compra_in.dict())

    # Obtener todos los productos del proveedor y crear detalles.
    # Calculamos el inventario anterior actual como la suma de cantidades existentes
    # y asignamos por defecto el inventario resultante = previo + cantidad_de_compra (actualmente 0).
    productos = Producto.objects.filter(proveedor_id=compra.proveedor_id)
    detalles_creados = []
    for producto in productos:
        prev = (
            DetalleCompra.objects.filter(producto=producto)
            .aggregate(total=Sum('cantidad'))
            .get('total')
        ) or 0
        cantidad_compra = 0
        inventario_resultante = prev + cantidad_compra
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=producto,
            cantidad=cantidad_compra,
            inventario_anterior=inventario_resultante,
        )
        detalles_creados.append(detalle)

    return _compra_to_dict(compra, detalles_creados)

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
    return _detalle_to_dict(detalle)


@compra_router.patch("/detalle/editar/{detalle_id}/", response=DetalleCompraSchema)
def editar_detalle(request, detalle_id: int, detalle_in: DetalleCompraUpdateSchema):
    """Edita un detalle de compra existente."""
    detalle = DetalleCompra.objects.get(id=detalle_id)
    # Actualizar solo los campos permitidos
    detalle.cantidad = detalle_in.cantidad
    detalle.inventario_anterior = detalle_in.inventario_anterior
    detalle.save()
    return _detalle_to_dict(detalle)

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
