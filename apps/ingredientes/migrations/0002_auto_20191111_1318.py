# Generated by Django 2.2.5 on 2019-11-11 18:18

from django.db import migrations

def insIngredientes(apps, schema_editor):
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing1 = ingrediente(nombre = "queso", valor = 1000)
	 ing1.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing2 = ingrediente(nombre = "piña", valor = 1000)
	 ing2.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing3 = ingrediente(nombre = "jamon", valor = 1000)
	 ing3.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing4 = ingrediente(nombre = "pollo", valor = 1000)
	 ing4.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing5 = ingrediente(nombre = "cabano", valor = 1000)
	 ing5.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing6 = ingrediente(nombre = "salami", valor = 1000)
	 ing6.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing7 = ingrediente(nombre = "champiñones", valor = 1000)
	 ing7.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing8 = ingrediente(nombre = "tocineta", valor = 1000)
	 ing8.save()
	 ingrediente = apps.get_model('ingredientes', 'ingrediente')
	 ing9 = ingrediente(nombre = "peperoni", valor = 1000)
	 ing9.save()
	 	

class Migration(migrations.Migration):

    dependencies = [
        ('ingredientes', '0001_initial'),
    ]

    operations = [migrations.RunPython(insIngredientes),
    ]