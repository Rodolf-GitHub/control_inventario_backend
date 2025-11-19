from django.db import models

# Create your models here.
class Tienda(models.Model):
    nombre = models.CharField(max_length=100,unique=True)
    class Meta:
        db_table = 'tienda'
    def __str__(self):
        return self.nombre
