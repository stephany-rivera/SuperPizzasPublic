	# Generated by Django 2.2.6 on 2019-11-05 01:49

from django.db import migrations


def insertarDatos(apps, schema_editor):
	 tipofranquicia = apps.get_model('franquicias', 'tipofranquicia')
	 plan1 = tipofranquicia(nombre = "basico", precio = 79000)
	 plan1.save()
	 tipofranquicia = apps.get_model('franquicias', 'tipofranquicia')
	 plan2 = tipofranquicia(nombre = "premium", precio = 135000)
	 plan2.save()
	 franquicia = apps.get_model('franquicias', 'franquicia')
	 FrPublic = franquicia(schema_name = "public", nombre = "public", tipo_id = 1)
	 FrPublic.save()
	 dominio = apps.get_model('franquicias', 'dominio')
	 DoGral = dominio(domain = "localhost", is_primary = True, tenant_id = 1)
	 DoGral.save()
		 
		 
class Migration(migrations.Migration):

	dependencies = [
		('franquicias', '0001_initial'),
	]
	
	operations = [
	migrations.RunPython(insertarDatos),
	
	]