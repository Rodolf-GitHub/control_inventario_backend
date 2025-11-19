from ninja import Schema,ModelSchema
from proveedor.models import Proveedor

class ProveedorSchema(ModelSchema):
    class Meta:
        model = Proveedor
        fields = '__all__'

class ProveedorInSchema(Schema):
    nombre: str
    tienda_id: int

class ProveedorUpdateSchema(Schema):
    nombre: str