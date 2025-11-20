from django.db import models

# Create your models here.
class Usuario(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    token = models.CharField(max_length=255, blank=True, null=True)
    es_superusuario = models.BooleanField(default=False)
    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return self.username

class PermisosUsuarioTienda(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tienda = models.ForeignKey('tienda.Tienda', on_delete=models.CASCADE)
    puede_gestionar_proveedores = models.BooleanField(default=True)
    puede_gestionar_productos = models.BooleanField(default=True)
    puede_gestionar_compras = models.BooleanField(default=True)
    puede_ver_inventario_compras = models.BooleanField(default=True)
    

    class Meta:
        db_table = 'permisos_usuario_tienda'
        constraints = [
            models.UniqueConstraint(fields=["usuario", "tienda"], name="unique_usuario_por_tienda"),
        ]
