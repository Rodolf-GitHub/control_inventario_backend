from ninja import Schema,ModelSchema
from compra.models import Compra,DetalleCompra
from datetime import date
from typing import Optional, Union

class CompraSchema(ModelSchema):
    class Meta:
        model = Compra
        fields = '__all__'

class CompraInSchema(Schema):
    proveedor_id: int
    fecha_compra: date

class CompraUpdateSchema(Schema):
    fecha_compra: date

class DetalleCompraSchema(Schema):
    id: int
    compra_id: int
    producto_id: int
    cantidad: int
    inventario_anterior: Union[int, str]
    producto_nombre: Optional[str] = None

class DetalleCompraInSchema(Schema):
    compra_id: int
    producto_id: int
    cantidad: int
    inventario_anterior: int

class DetalleCompraUpdateSchema(Schema):
    cantidad: Optional[int] = None
    inventario_anterior: Optional[int] = None

class CompraWithDetailsSchema(CompraSchema):
    detalles: list[DetalleCompraSchema]