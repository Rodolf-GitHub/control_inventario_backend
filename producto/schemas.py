from ninja import Schema,ModelSchema
from producto.models import Producto

class ProductoSchema(ModelSchema):
    class Meta:
        model = Producto
        fields = '__all__'

class ProductoInSchema(Schema):
    nombre: str
    proveedor_id: int