from ninja import Router
from compra.schemas import (
    CompraSchema,
    CompraInSchema,
    DetalleCompraSchema,
    DetalleCompraInSchema,
    DetalleCompraUpdateSchema,
    CompraWithDetailsSchema,
)
from compra.models import Compra, DetalleCompra
from producto.models import Producto
from datetime import date
from typing import Optional

compra_router = Router(tags=["Compras"])

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
        detalles = DetalleCompra.objects.filter(compra=compra)
        compra_data = CompraWithDetailsSchema.from_orm(compra)
        compra_data.detalles = [DetalleCompraSchema.from_orm(d) for d in detalles]
        resultado.append(compra_data)
    return resultado



@compra_router.post("/crear/", response=CompraWithDetailsSchema)
def crear_compra(request, compra_in: CompraInSchema):
    """Crea una nueva compra y genera un detalle por cada producto del proveedor con valores en 0."""
    compra = Compra.objects.create(**compra_in.dict())

    # Obtener todos los productos del proveedor y crear detalles con valores en 0
    productos = Producto.objects.filter(proveedor_id=compra.proveedor_id)
    detalles_creados = []
    for producto in productos:
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=producto,
            cantidad=0,
            inventario_anterior=0,
        )
        detalles_creados.append(detalle)

    compra_data = CompraWithDetailsSchema.from_orm(compra)
    compra_data.detalles = [DetalleCompraSchema.from_orm(d) for d in detalles_creados]
    return compra_data


@compra_router.patch("/detalle/editar/{detalle_id}/", response=DetalleCompraSchema)
def editar_detalle(request, detalle_id: int, detalle_in: DetalleCompraUpdateSchema):
    """Edita un detalle de compra existente."""
    detalle = DetalleCompra.objects.get(id=detalle_id)
    # Actualizar solo los campos permitidos
    detalle.cantidad = detalle_in.cantidad
    detalle.inventario_anterior = detalle_in.inventario_anterior
    detalle.save()
    return detalle





@compra_router.delete("/eliminar/{compra_id}/")
def eliminar_compra(request, compra_id: int):
    """Elimina una compra (y sus detalles por cascade)."""
    compra = Compra.objects.get(id=compra_id)
    compra.delete()
    return {"mensaje": "Compra eliminada correctamente."}
