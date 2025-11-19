from django.db import models

# Create your models here.
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    tienda = models.ForeignKey('tienda.Tienda', on_delete=models.CASCADE)

    class Meta:
        db_table = 'proveedor'
        constraints = [
            models.UniqueConstraint(fields=["tienda", "nombre"], name="unique_proveedor_por_tienda"),
        ]
        
    def __str__(self):
        return self.nombre
