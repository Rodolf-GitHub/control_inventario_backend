from django.db import models

# Create your models here.
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    proveedor = models.ForeignKey('proveedor.Proveedor', on_delete=models.CASCADE)

    class Meta:
        db_table = 'producto'

    def __str__(self):
        return self.nombre
