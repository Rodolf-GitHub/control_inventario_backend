from ninja import NinjaAPI
from tienda.api import tienda_router
from compra.api import compra_router
from proveedor.api import proveedor_router
from producto.api import producto_router


api = NinjaAPI(title="Control Inventario API")

# Registrar routers de las distintas apps
api.add_router("/tienda/", tienda_router)
api.add_router("/compra/", compra_router)
api.add_router("/proveedor/", proveedor_router)
api.add_router("/producto/", producto_router)


# Puedes añadir más routers aquí: api.add_router('/otra/', otra_router)
