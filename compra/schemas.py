from ninja import Schema,ModelSchema
from compra.models import Compra,DetalleCompra
from datetime import date
from typing import Optional

class CompraSchema(ModelSchema):
    class Meta:
        model = Compra
        fields = '__all__'

class CompraInSchema(Schema):
    proveedor_id: int
    fecha_compra: date

class DetalleCompraSchema(ModelSchema):
    producto_nombre: Optional[str] = None
    class Meta:
        model = DetalleCompra
        fields = '__all__'
    @staticmethod
    def resolve_producto_nombre(detalle: DetalleCompra):
        return detalle.producto.nombre if detalle.producto else None

class DetalleCompraInSchema(Schema):
    compra_id: int
    producto_id: int
    cantidad: int
    inventario_anterior: int

class DetalleCompraUpdateSchema(Schema):
    cantidad: int
    inventario_anterior: int

class CompraWithDetailsSchema(CompraSchema):
    detalles: list[DetalleCompraSchema]