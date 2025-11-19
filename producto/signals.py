from django.db.models.signals import post_save
from django.dispatch import receiver
from producto.models import Producto
from compra.models import Compra, DetalleCompra

@receiver(post_save, sender=Producto)
def crear_detalle_en_compras(sender, instance, created, **kwargs):
    """Al crear un Producto, crear un DetalleCompra (cantidad=0, inventario_anterior=0)
    para todas las compras existentes si no existe ya un detalle para esa compra y producto.
    """
    if not created:
        return

    compras = Compra.objects.all()
    detalles_to_create = []
    for compra in compras:
        # evitar duplicados
        if DetalleCompra.objects.filter(compra=compra, producto=instance).exists():
            continue
        detalles_to_create.append(DetalleCompra(compra=compra, producto=instance, cantidad=0, inventario_anterior=0))

    if detalles_to_create:
        DetalleCompra.objects.bulk_create(detalles_to_create)
