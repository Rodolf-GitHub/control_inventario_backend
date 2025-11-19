from ninja import Schema,ModelSchema
from tienda.models import Tienda

class TiendaSchema(ModelSchema):
    class Meta:
        model = Tienda
        fields = '__all__'

class TiendaInSchema(Schema):
    nombre: str