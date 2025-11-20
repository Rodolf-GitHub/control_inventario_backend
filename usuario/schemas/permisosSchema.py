from ninja import Schema,ModelSchema
from usuario.models import Usuario, PermisosUsuarioTienda
from typing import Optional

class PermisosUsuarioTiendaSchema(ModelSchema):
    class Meta:
        model = PermisosUsuarioTienda
        fields = '__all__'

class PermisosUsuarioTiendaInSchema(Schema):
    tienda_id: int
    puede_gestionar_proveedores: bool = True
    puede_gestionar_productos: bool = True
    puede_gestionar_compras: bool = True
    puede_editar_compras: bool = True
    puede_ver_inventario_compras: bool = True

class PermisosUsuarioTiendaUpdateSchema(Schema):
    puede_gestionar_proveedores: bool
    puede_gestionar_productos: bool
    puede_gestionar_compras: bool
    puede_editar_compras: bool
    puede_ver_inventario_compras: bool