from ninja import NinjaAPI
from usuario.auth import AuthBearer
from tienda.api import tienda_router
from compra.api import compra_router
from proveedor.api import proveedor_router
from producto.api import producto_router
from usuario.apis.usuarios_y_login import usuario_router
from usuario.apis.permisos import permisos_router


api = NinjaAPI(title="Control Inventario API", auth=AuthBearer())

# Registrar routers de las distintas apps
api.add_router("/tienda/", tienda_router)
api.add_router("/compra/", compra_router)
api.add_router("/proveedor/", proveedor_router)
api.add_router("/producto/", producto_router)

# Router para la gestión de usuarios (login / creación por superadmin)
api.add_router("/usuario/", usuario_router)
# Router para gestión de permisos por tienda (solo superadmin)
api.add_router("/usuario/permisos/", permisos_router)


# Puedes añadir más routers aquí: api.add_router('/otra/', otra_router)
