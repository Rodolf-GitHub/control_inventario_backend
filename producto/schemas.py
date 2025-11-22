from ninja import Schema, ModelSchema
from producto.models import Producto
from typing import Optional, Literal

class ProductoSchema(ModelSchema):
    class Meta:
        model = Producto
        fields = '__all__'

class ProductoInSchema(Schema):
    nombre: str
    proveedor_id: int
    orden: Optional[int] = 999

class ProductoUpdateSchema(Schema):
    nombre: str
    orden: Optional[int] = None

class MoverProductoSchema(Schema):
    producto_id: int
    direccion: Literal['arriba', 'abajo']
    