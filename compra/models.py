from django.db import models
from django.utils import timezone
# Create your models here.

class Compra(models.Model):
    proveedor = models.ForeignKey('proveedor.Proveedor', on_delete=models.CASCADE)
    fecha_compra = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'compra'
        constraints = [
            models.UniqueConstraint(fields=["proveedor", "fecha_compra"], name="unique_compra_proveedor_fecha"),
        ]

class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey('producto.Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    inventario_anterior = models.PositiveIntegerField()

    class Meta:
        db_table = 'detalle_compra'
        constraints = [
            models.UniqueConstraint(fields=["compra", "producto"], name="unique_producto_por_compra"),
        ]
