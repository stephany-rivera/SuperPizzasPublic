from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=50)
    ingrediente = models.ManyToManyField('ingredientes.Ingrediente')
    valor = models.BigIntegerField()
    def __str__(self):
        return self.nombre
